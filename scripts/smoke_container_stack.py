"""Exercise the real container/proxy/worker/export path with original fixture art.

Engineering fixture script approval is not owner creative acceptance. No watched
confirmation, publishing request, network provider or external artwork is used.
"""
import hashlib
import http.cookiejar
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='http://127.0.0.1:3000'

def main():
    values=dict(line.split('=',1) for line in (ROOT/'.env.local').read_text().splitlines() if line.startswith('FNS_'))
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf=''
    def request(method,path,body=None,headers=None):
        data=None if body is None else json.dumps(body).encode()
        outgoing={'Origin':ORIGIN,'Content-Type':'application/json','X-CSRF-Token':csrf,'Idempotency-Key':str(uuid4())}
        outgoing.update(headers or {})
        return opener.open(urllib.request.Request(ORIGIN+path,data=data,method=method,headers=outgoing),timeout=10)
    def api(method,path,body=None):
        with request(method,'/api/v1/'+path,body) as response:
            raw=response.read();return json.loads(raw) if raw else None
    deadline=time.monotonic()+90
    while True:
        try:
            if api('GET','healthz')['service']=='v2manhwa-local':break
        except (OSError,ValueError,KeyError):pass
        if time.monotonic()>deadline:raise RuntimeError('Container stack did not become healthy')
        time.sleep(1)
    with request('GET','/') as page:
        if b'Flamingo' not in page.read():raise RuntimeError('Studio HTML did not render')
    try:
        api('GET','studio/episodes')
        raise AssertionError('Anonymous studio request should be rejected')
    except urllib.error.HTTPError as error:
        assert error.code==401
    csrf=api('POST','auth/login',{'key':values['FNS_LOCAL_DEV_KEY']})['csrf']
    try:
        record=api('POST','studio/demo-episode')
        record=api('POST',f"studio/episodes/{record['id']}/approve-script",{'revision':record['revision'],'confirmed_source_review':True})
        job=api('POST',f"studio/episodes/{record['id']}/render",{'revision':record['revision']})
        deadline=time.monotonic()+120
        while True:
            jobs=api('GET',f"studio/episodes/{record['id']}/render-jobs")
            current=next(item for item in jobs if item['id']==job['id'])
            if current['state']=='completed':break
            if current['state'] in ('failed','cancelled'):raise RuntimeError('Fixture render failed: '+str(current.get('error')))
            if time.monotonic()>deadline:raise RuntimeError('Fixture render did not finish')
            time.sleep(1)
        record=api('GET',f"studio/episodes/{record['id']}")
        export=record['export'];assert record['qa']['status']=='PASS'
        assert len(export['manifest']['shots'])==3
        assert (export['width'],export['height'])==(1280,720)
        signed=api('GET',f"studio/episodes/{record['id']}/export-url")
        with request('GET',signed['url'],headers={'Range':'bytes=0-31'}) as response:
            assert response.status==206 and response.headers['Content-Range'].startswith('bytes 0-31/')
            assert response.read()[4:8]==b'ftyp'
        with request('GET',signed['url']) as response:
            assert hashlib.sha256(response.read()).hexdigest()==export['sha256']
        captions=api('GET',f"studio/episodes/{record['id']}/export-url?asset=captions")
        with request('GET',captions['url']) as response:assert response.read().startswith(b'WEBVTT')
        beats=record['beats'];beats[0]['spoken_text']+=' The signal is clear.'
        edited=api('PUT',f"studio/episodes/{record['id']}/script",{'revision':record['revision'],'beats':beats,'voice':record['voice'],'notes':'Container engineering fixture; not owner creative acceptance.'})
        assert edited['export'] is None and edited['script_approval'] is None
        try:
            api('GET',f"studio/episodes/{record['id']}/export-url")
            raise AssertionError('Edited script must not expose the stale export')
        except urllib.error.HTTPError as error:assert error.code==409
        report={'status':'PASS_CONTAINER_HTTP_FLOW','production_id':record['id'],'job_id':job['id'],
                'duration_seconds':export['duration_seconds'],'export_sha':export['sha256'],
                'boundaries':['studio_html','anonymous_denial','session_and_csrf','source_fixture_import','script_revision','durable_worker','private_export_hash','byte_range','captions','edit_invalidates_export'],
                'browser_verified':False,'owner_creative_approval':False,'published':False}
        (ROOT/'work').mkdir(exist_ok=True);(ROOT/'work/container-smoke.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:api('POST','auth/logout')

if __name__=='__main__':main()
