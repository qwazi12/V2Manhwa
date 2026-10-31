"""Signed private LOCAL snapshots and a disposable database/object restore drill.

Run with this repository's .env.local sourced and PYTHONPATH=api. Keys and active
sessions are excluded. A snapshot verifies only with its independent signing key.
This is not a cloud backup or a production disaster recovery procedure.
"""
import argparse
from dataclasses import replace
from datetime import datetime,timezone
import hashlib,hmac,json,os,re,subprocess,tempfile
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse
from sqlalchemy import text
from flamingo_next_api.config import Settings
from flamingo_next_api.database import engine_for
from flamingo_next_api.storage import Storage

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['bash',str(ROOT/'scripts/docker_local.sh'),'compose','-f',str(ROOT/'compose.yaml'),'-f',str(ROOT/'compose.app.yaml')]
TABLES=('studio_episodes','studio_snapshots','source_pages','media_assets','canon_claims','studio_render_jobs')

def execute(args,**kwargs):
    return subprocess.run(args,cwd=ROOT,check=True,stderr=subprocess.PIPE,timeout=120,**kwargs)

def owned_resources():
    for service in ('postgres','minio'):
        cid=execute(COMPOSE+['ps','-q',service],capture_output=False,stdout=subprocess.PIPE).stdout.decode().strip()
        if not cid:raise RuntimeError('Start this independent Compose stack before snapshotting')
        state=json.loads(execute(['docker','inspect',cid],stdout=subprocess.PIPE).stdout)[0]
        labels=state['Config']['Labels']
        if labels.get('com.docker.compose.project')!='v2manhwa-local' or labels.get('com.docker.compose.service')!=service:
            raise RuntimeError('Snapshot refuses an unrecognized container')
        port='5432/tcp' if service=='postgres' else '9000/tcp'
        expected='56473' if service=='postgres' else '59473'
        if not any(p['HostIp']=='127.0.0.1' and p['HostPort']==expected for p in state['NetworkSettings']['Ports'].get(port,[])):
            raise RuntimeError('Snapshot refuses unexpected host bindings')

def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):result.update(block)
    return result.hexdigest()

def signature(manifest,key):
    return hmac.new(key.encode(),json.dumps(manifest,sort_keys=True).encode(),hashlib.sha256).hexdigest()

def dedicated(settings):
    db=urlparse(settings.database_url);storage=urlparse(settings.storage_endpoint)
    if db.hostname not in ('127.0.0.1','localhost') or db.port!=56473 or db.path!='/fns_local' or db.username!='fns_local' or storage.hostname not in ('127.0.0.1','localhost') or storage.port!=59473 or storage.scheme!='http' or settings.bucket!='v2manhwa-synthetic':
        raise ValueError('Snapshot requires this exact independent local database and bucket')

def create(settings):
    dedicated(settings);owned_resources();store=Storage(settings)
    parent=ROOT/'work/backups';parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-'),dir=parent))
    os.chmod(path,0o700);(path/'objects').mkdir(mode=0o700)
    # Block concurrent product writes while obtaining the DB + object manifest.
    engine=engine_for(settings)
    try:
        with engine.begin() as conn:
            conn.execute(text('LOCK TABLE studio_episodes,studio_snapshots,media_assets,studio_render_jobs,studio_commands IN SHARE MODE'))
            counts={table:conn.execute(text(f'SELECT count(*) FROM {table}')).scalar_one() for table in TABLES}
            dump=path/'database.dump'
            with dump.open('wb') as output:
                execute(COMPOSE+['exec','-T','postgres','pg_dump','-U','fns_local','-Fc','--no-owner','--exclude-table-data=local_sessions','fns_local'],stdout=output)
            os.chmod(dump,0o600)
            objects=[]
            for page in store.client.get_paginator('list_objects_v2').paginate(Bucket=settings.bucket):
                for obj in page.get('Contents',[]):
                    key=obj['Key'];name=hashlib.sha256(key.encode()).hexdigest();target=path/'objects'/name
                    store.client.download_file(settings.bucket,key,str(target));os.chmod(target,0o600)
                    objects.append({'key':key,'file':name,'sha256':digest(target),'size_bytes':target.stat().st_size})
            manifest={'version':1,'created_at':datetime.now(timezone.utc).isoformat(),'project':'v2manhwa-local','database_sha256':digest(dump),'table_counts':counts,'objects':objects,'sessions_included':False}
            manifest['signature']=signature(manifest,settings.signing_key)
            (path/'manifest.json').write_text(json.dumps(manifest,indent=2));os.chmod(path/'manifest.json',0o600)
    finally:engine.dispose()
    return path

def verify(settings,path):
    dedicated(settings);owned_resources();manifest=json.loads((path/'manifest.json').read_text());signed=manifest.pop('signature')
    if manifest.get('project')!='v2manhwa-local' or not hmac.compare_digest(signed,signature(manifest,settings.signing_key)):
        raise ValueError('Snapshot signature is invalid; no restore attempted')
    if digest(path/'database.dump')!=manifest['database_sha256']:raise ValueError('Database checksum mismatch')
    for obj in manifest['objects']:
        if not re.fullmatch('[0-9a-f]{64}',obj['file']):raise ValueError('Invalid snapshot object filename')
        target=path/'objects'/obj['file']
        if target.stat().st_size!=obj['size_bytes'] or digest(target)!=obj['sha256']:raise ValueError('Object checksum mismatch')
    nonce=uuid4().hex[:16];dbname='fns_restore_'+nonce;bucket='v2manhwa-restore-'+nonce
    store=Storage(replace(settings,bucket=bucket));created_db=False;created_bucket=False
    try:
        execute(COMPOSE+['exec','-T','postgres','createdb','-U','fns_local',dbname]);created_db=True
        with (path/'database.dump').open('rb') as source:
            execute(COMPOSE+['exec','-T','postgres','pg_restore','-U','fns_local','--no-owner','--exit-on-error','-d',dbname],stdin=source)
        output=execute(COMPOSE+['exec','-T','postgres','psql','-U','fns_local','-d',dbname,'-tAc','SELECT json_build_object('+','.join(f"'{table}',(SELECT count(*) FROM {table})" for table in TABLES)+")"],stdout=subprocess.PIPE).stdout
        if json.loads(output)!=manifest['table_counts']:raise RuntimeError('Restored product table counts differ')
        sessions=execute(COMPOSE+['exec','-T','postgres','psql','-U','fns_local','-d',dbname,'-tAc','SELECT count(*) FROM local_sessions'],stdout=subprocess.PIPE).stdout.strip()
        if sessions!=b'0':raise RuntimeError('Active sessions should not survive a restore')
        store.initialize();created_bucket=True
        for obj in manifest['objects']:
            target=path/'objects'/obj['file'];store.client.upload_file(str(target),bucket,obj['key'])
            streamed=store.client.get_object(Bucket=bucket,Key=obj['key'])['Body'];value=hashlib.sha256()
            for block in iter(lambda:streamed.read(1024*1024),b''):value.update(block)
            if value.hexdigest()!=obj['sha256']:raise RuntimeError('Restored object bytes differ')
        return {'status':'PASS_LOCAL_RESTORE','objects_verified':len(manifest['objects']),'table_counts':manifest['table_counts'],'active_sessions_restored':0,'cloud_restore':'NOT_RUN'}
    finally:
        if created_bucket:
            for page in store.client.get_paginator('list_objects_v2').paginate(Bucket=bucket):
                keys=[{'Key':obj['Key']} for obj in page.get('Contents',[])]
                if keys:store.client.delete_objects(Bucket=bucket,Delete={'Objects':keys})
            store.client.delete_bucket(Bucket=bucket)
        if created_db:execute(COMPOSE+['exec','-T','postgres','dropdb','-U','fns_local',dbname])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['create','verify']);parser.add_argument('snapshot',nargs='?');args=parser.parse_args()
    settings=Settings.load()
    if args.action=='create':print(create(settings))
    else:
        if not args.snapshot:parser.error('verify requires a snapshot directory')
        print(json.dumps(verify(settings,Path(args.snapshot)),indent=2))
