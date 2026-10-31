"""Import an authorized local draft through the API, without approving or rendering it."""
import argparse
import base64
import hashlib
import http.cookiejar
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'api'))
from flamingo_next_api.config import Settings
from flamingo_next_api.product_db import sha
from flamingo_next_api.product_models import SourceInput, EditInput

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--series-id')
    group.add_argument('--new-series')
    parser.add_argument('--chapter',required=True)
    args=parser.parse_args()
    settings=Settings.load();origin=settings.web_origin
    if origin!='http://127.0.0.1:3000':raise ValueError('Use only this project loopback studio')
    plan=json.loads(args.plan.read_text());draft=plan['record']
    if draft.get('script_approval') or draft.get('review'):raise ValueError('Owner approvals cannot be imported')
    manifest=json.loads((args.plan.parent/'source-manifest.json').read_text())
    key='authorized-draft-'+sha({'source':manifest,'chapter':args.chapter})[:40]
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf=''
    def api(method,path,body=None,step=''):
        data=None if body is None else json.dumps(body).encode()
        if data and len(data)>45_000_000:raise ValueError('Request exceeds studio body limit')
        headers={'Origin':origin,'Content-Type':'application/json','X-CSRF-Token':csrf,'Idempotency-Key':key+'-'+step}
        request=urllib.request.Request(origin+'/api/v1/'+path,data=data,method=method,headers=headers)
        try:
            with opener.open(request,timeout=180) as response:
                raw=response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'Studio request failed ({error.code}): {error.read(1500).decode(errors="replace")}') from None
    health=api('GET','healthz')
    if health.get('service')!='v2manhwa-local':raise ValueError('Not this project studio')
    csrf=api('POST','auth/login',{'key':settings.owner_key},'login')['csrf']
    try:
        series_id=args.series_id or api('POST','studio/series',{'title':args.new_series,'language':'en','aliases':[]},'series')['id']
        pages=[]
        for page in manifest['pages']:
            source=(args.plan.parent/page['filename']).resolve()
            if not source.is_relative_to(args.plan.parent.resolve()):raise ValueError('Invalid source path')
            raw=source.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=page['sha256']:raise ValueError('Original source checksum changed')
            # OCR was not owner-transcribed. Preserve it separately, not as approved text.
            pages.append({'order':page['order'],'filename':page['filename'],'kind':'story','text':'','data_base64':base64.b64encode(raw).decode()})
        body=SourceInput.model_validate({'series_id':series_id,'chapter_key':args.chapter,'title':'Chapter '+args.chapter,'rights':draft['rights'],'pages':pages}).model_dump(mode='json')
        imported=api('POST','studio/sources',body,'source')
        current=api('GET','studio/episodes/'+imported['id'])
        if current['beats']:raise ValueError('A saved script already exists; open it in the studio to avoid overwriting edits')
        by_order={page['order']:page['id'] for page in current['pages']}
        draft_order={page['id']:page['order'] for page in draft['pages']}
        beats=[beat|{'page_id':by_order[draft_order[beat['page_id']]]} for beat in draft['beats']]
        edit=EditInput.model_validate({'revision':current['revision'],'beats':beats,'voice':draft['voice'],'notes':'Assisted draft; source/voice/creative owner review pending. No script approval or release granted. Source: '+plan['provenance']['source_url']})
        saved=api('PUT','studio/episodes/'+current['id']+'/script',edit.model_dump(mode='json'),'script')
        print(json.dumps({'production_id':saved['id'],'revision':saved['revision'],'status':saved['status'],'pages':len(saved['pages']),'beats':len(saved['beats']),'script_approved':False,'published':False},indent=2))
    finally:
        api('POST','auth/logout',None,'logout')

if __name__=='__main__':main()
