"""Render a local, unapproved review artifact with the production media engine.

This engineering utility does not modify application state or grant approval.
The plan and authorized artwork stay outside Git in work/. No network calls.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'api'))
from botocore.exceptions import ClientError
from flamingo_next_api.media_engine import MediaEngine
from flamingo_next_api.product_models import BeatInput, RightsInput
from flamingo_next_api.storage import Storage

class LocalObjects:
    def __init__(self,root):self.root=root
    def path(self,key):
        path=(self.root/key).resolve()
        if not path.is_relative_to(self.root.resolve()):raise ValueError('Invalid local object path')
        return path
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        target=self.path(Key);target.parent.mkdir(parents=True,exist_ok=True)
        data=Body.read() if hasattr(Body,'read') else Body
        temporary=target.with_suffix(target.suffix+'.incoming')
        temporary.write_bytes(data);temporary.replace(target)
    def get_object(self,*,Bucket,Key):
        target=self.path(Key)
        if not target.is_file():raise ClientError({'Error':{'Code':'NoSuchKey'}},'GetObject')
        return {'Body':io.BytesIO(target.read_bytes())}

class DraftEngine(MediaEngine):
    def speech(self,text,folder,index,profile='system-default'):
        print(f'Preparing narration and shot {index+1}',flush=True)
        return super().speech(text,folder,index,profile)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    plan=json.loads(args.plan.read_text());record=plan['record']
    rights=RightsInput.model_validate(record['rights'])
    if not rights.allow_internal or rights.basis=='unknown':raise ValueError('Documented processing rights required')
    if record.get('script_approval') or record.get('review'):raise ValueError('Draft plans must not claim owner approval')
    record['beats']=[BeatInput.model_validate(beat).model_dump(mode='json') for beat in record['beats']]
    pages={p['id']:p for p in record['pages']}
    if len(pages)!=len(record['pages']) or any(b['page_id'] not in pages for b in record['beats']):raise ValueError('Invalid source-page links')
    cache=ROOT/'work/private-draft-cache';cache.mkdir(parents=True,exist_ok=True,mode=0o700)
    keyfile=cache/'signing-key'
    if not keyfile.exists():
        fd=os.open(keyfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as file:file.write(secrets.token_hex(32))
    storage=Storage.__new__(Storage)
    storage.settings=SimpleNamespace(bucket='local-draft-only',signing_key=keyfile.read_text())
    storage.client=LocalObjects(cache/'objects')
    assets={}
    for page in record['pages']:
        source=(args.plan.parent/page['local_file']).resolve()
        if not source.is_relative_to(args.plan.parent.resolve()):raise ValueError('Source must be inside the plan directory')
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=page['sha256']:raise ValueError('Authorized source checksum changed')
        blob=storage.put_blob(raw,'image/png')
        assets[page['asset_id']]={'object_key':blob['key'],'sha256':blob['sha256']}
    result=DraftEngine(storage).render(record,assets)
    args.output.mkdir(parents=True,exist_ok=True)
    export=result['export']
    for name,blob in [('chapter-1-private-draft.mp4',export),('chapter-1-narration.wav',export['voice_blob']),('chapter-1-captions.vtt',export['captions_blob']),('chapter-1-shot-manifest.json',export['manifest_blob'])]:
        (args.output/name).write_bytes(storage.read_blob(blob['key'],blob['sha256']))
    report={'status':'DRAFT_HUMAN_REVIEW_REQUIRED','application_imported':False,'owner_watched':False,
            'publication_authorized':False,'reference_video_playback_verified':False,
            'source_provenance':plan['provenance'],'technical_qa':result['qa'],
            'duration_seconds':export['duration_seconds'],'width':export['width'],'height':export['height'],
            'export_sha256':export['sha256'],'beats':len(record['beats'])}
    (args.output/'chapter-1-review-report.json').write_text(json.dumps(report,indent=2))
    shutil.copyfile(args.plan,args.output/'chapter-1-draft-plan.json')
    print(json.dumps({k:report[k] for k in ('status','duration_seconds','width','height','beats')}),flush=True)

if __name__=='__main__':main()
