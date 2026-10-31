"""Full product security/editorial/real media validation in isolated test resources."""
from pathlib import Path
from uuid import uuid4,UUID
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
import copy,json,time
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select,text,update
from flamingo_next_api.main import create_app
from flamingo_next_api.product_db import ProductDB
from flamingo_next_api.ingestion import Ingestion,normalize
from flamingo_next_api.editorial import Editorial,input_fingerprint
from flamingo_next_api.product_models import SeriesInput,SourceInput,EditInput,ScriptApproval,RevisionInput,PackageInput,ReviewInput
from flamingo_next_api.demo_episode import create_demo,fixture_pages,STORY
from flamingo_next_api.render_jobs import RenderJobs
from flamingo_next_api.production_worker import run_once
from flamingo_next_api.database import engine_for
from flamingo_next_api.storage import Storage
from test_demo_api import settings,auth

@pytest.fixture
def product(settings):
    engine=engine_for(settings)
    command.upgrade(Config(str(Path(__file__).resolve().parents[1]/'api/alembic.ini')),'head')
    with engine.begin() as conn:
        conn.execute(text('TRUNCATE works,media_assets,rights_manifests,research_candidates,analytics_observations,studio_commands,audit_events,outbox_events CASCADE'))
    store=Storage(settings);store.initialize();db=ProductDB(engine)
    with TestClient(create_app(settings)) as client:
        yield client,db,store
    engine.dispose()

def sample(db,store,key=None):return create_demo(Ingestion(db,store),Editorial(db),key or str(uuid4()))
def approved(db,store):
    episode=sample(db,store)
    return Editorial(db).approve_script(episode['id'],ScriptApproval(revision=episode['revision'],confirmed_source_review=True),str(uuid4()))

def test_identity_and_ingestion_are_real_and_idempotent(product):
    client,db,store=product;headers=auth(client)
    body={'title':'Same name','aliases':['동일 이름','Ｄｅｍｏ']}
    first=client.post('/api/v1/studio/series',json=body,headers=headers)
    assert first.status_code==201,first.text
    assert client.post('/api/v1/studio/series',json=body,headers=headers).json()['id']==first.json()['id']
    headers['Idempotency-Key']=str(uuid4())
    second=client.post('/api/v1/studio/series',json=body,headers=headers).json()
    assert first.json()['id']!=second['id']
    assert normalize('Ｄｅｍｏ')==normalize('demo')
    record=sample(db,store,'product-idempotent-demo')
    assert sample(db,store,'product-idempotent-demo')['id']==record['id']
    assert len(record['pages'])==3 and len(record['beats'])==3
    assert all(p['panel_id'] and p['asset_id'] for p in record['pages'])
    assert Editorial(db).snapshots(record['id'])
    private=client.get(f"/api/v1/studio/assets/{record['pages'][0]['asset_id']}/signed-url").json()['url']
    assert client.get(private).headers['content-type'].startswith('image/png')
    client.cookies.clear();assert client.get(private).status_code==401

def test_ingestion_rejects_rights_missing_order_and_malicious_media(product):
    _,db,store=product;ing=Ingestion(db,store)
    series=ing.series(SeriesInput(title='Upload security'),str(uuid4()))
    body={'series_id':series['id'],'chapter_key':'1','title':'Fixture','rights':{'basis':'unknown','rightsholder':'Fixture','evidence':'Test fixture','allow_internal':False},'pages':fixture_pages()}
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as err:ing.import_source(SourceInput.model_validate(body),str(uuid4()))
    assert err.value.status_code==403
    body['rights'].update(basis='original',allow_internal=True)
    invalid=copy.deepcopy(body);invalid['pages'][1]['order']=4
    with pytest.raises(HTTPException):ing.import_source(SourceInput.model_validate(invalid),str(uuid4()))
    invalid=copy.deepcopy(body);invalid['pages'][0]['filename']='../escape.png'
    with pytest.raises(HTTPException):ing.import_source(SourceInput.model_validate(invalid),str(uuid4()))
    invalid=copy.deepcopy(body);invalid['pages'][0]['data_base64']='PHN2Zz48c2NyaXB0Lz48L3N2Zz4='
    with pytest.raises(HTTPException):ing.import_source(SourceInput.model_validate(invalid),str(uuid4()))
    record=ing.import_source(SourceInput.model_validate(body),str(uuid4()))
    with pytest.raises(HTTPException) as err:ing.import_source(SourceInput.model_validate(body),str(uuid4()))
    assert err.value.status_code==409

def test_script_evidence_revision_coverage_and_approval_invalidation(product):
    _,db,store=product;editor=Editorial(db);record=sample(db,store)
    from fastapi import HTTPException
    body=EditInput.model_validate({'revision':record['revision'],'beats':record['beats']})
    body.beats[0].page_id=uuid4()
    with pytest.raises(HTTPException):editor.edit(record['id'],body,str(uuid4()))
    body=EditInput.model_validate({'revision':record['revision'],'beats':record['beats'][:1]})
    changed=editor.edit(record['id'],body,str(uuid4()))
    with pytest.raises(HTTPException):editor.approve_script(record['id'],ScriptApproval(revision=changed['revision'],confirmed_source_review=True),str(uuid4()))
    with pytest.raises(HTTPException):editor.edit(record['id'],body,str(uuid4()))
    body=EditInput.model_validate({'revision':changed['revision'],'beats':record['beats']})
    changed=editor.edit(record['id'],body,str(uuid4()))
    approved_record=editor.approve_script(record['id'],ScriptApproval(revision=changed['revision'],confirmed_source_review=True),str(uuid4()))
    assert approved_record['script_approval']['input_sha']==input_fingerprint(approved_record)
    body=EditInput.model_validate({'revision':approved_record['revision'],'beats':record['beats']})
    body.beats[0].spoken_text+=' A correction.'
    changed=editor.edit(record['id'],body,str(uuid4()))
    assert changed['script_approval'] is None and changed['export'] is None and changed['review'] is None
    assert len(editor.snapshots(record['id']))>=5

def test_render_claim_cancel_retry_and_stale_worker_fencing(product):
    _,db,store=product;record=approved(db,store);jobs=RenderJobs(db)
    job=jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    with ThreadPoolExecutor(4) as pool:claims=list(pool.map(lambda _:jobs.claim(),range(4)))
    assert sum(j is not None for j in claims)==1
    claim=next(j for j in claims if j)
    jobs.cancel(claim['id'],str(uuid4()));assert not jobs.heartbeat(claim['id'],claim['lease_token'])
    assert jobs.finish(claim,error='late result') is False
    jobs.retry(claim['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    newer=jobs.claim();assert newer['lease_token']!=claim['lease_token']
    assert not jobs.finish(claim,error='superseded')
    jobs.finish(newer,error='Deliberate fixture failure')
    assert jobs.list(record['id'])[0]['state']=='failed'

@pytest.mark.media
def test_real_narration_export_qa_range_package_review_and_invalidation(product):
    client,db,store=product;headers=auth(client);record=approved(db,store);jobs=RenderJobs(db)
    job=jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    assert run_once(db,store)
    record=Editorial(db).get(record['id'])
    assert record['status']=='MEDIA_REVIEW',jobs.list(record['id'])
    assert record['qa']['status']=='PASS' and record['qa']['semantic_qa']=='HUMAN_REVIEW_REQUIRED'
    assert record['export']['duration_seconds']>3
    link=client.get(f"/api/v1/studio/episodes/{record['id']}/export-url").json()['url']
    response=client.get(link,headers={'Range':'bytes=0-99'})
    assert response.status_code==206 and len(response.content)==100
    assert client.get(link.replace('signature=','signature=bad')).status_code==403
    record=Editorial(db).package(record['id'],PackageInput(revision=record['revision'],title='The signal answered',description='An original story about a keeper following a signal.'),str(uuid4()))
    before=record['revision']
    record=Editorial(db).review(record['id'],ReviewInput(revision=before,confirmed_watched=True,confirmed_rights=True,decision='approve',notes='Automated fixture review only; not owner acceptance.'),str(uuid4()))
    assert record['status']=='APPROVED_PRIVATE'
    assert client.get('/api/v1/studio/publishing').json()['items'][0]['approval_current'] is True
    assert client.post(f"/api/v1/studio/episodes/{record['id']}/publish",headers=headers).status_code==403
    record=Editorial(db).package(record['id'],PackageInput(revision=record['revision'],title='A changed promise',description='A revised owner description.'),str(uuid4()))
    assert record['review'] is None
    assert client.get('/api/v1/studio/publishing').json()['items'][0]['approval_current'] is False
    body=EditInput.model_validate({'revision':record['revision'],'beats':record['beats']})
    body.beats[0].spoken_text+=' Changed narration.'
    record=Editorial(db).edit(record['id'],body,str(uuid4()))
    assert client.get(f"/api/v1/studio/episodes/{record['id']}/export-url").status_code==409
    assert record['packaging']['title']=='A changed promise' and record['packaging']['title_locked'] is True

def test_manual_research_preserves_unknowns_and_actual_intervals(product):
    client,db,store=product;headers=auth(client)
    now=datetime.now(timezone.utc)-timedelta(hours=1)
    body={'title':'Observed candidate','video_id':'fixture-video-1','source_url':'https://example.com/observed-video','observed_at':(now-timedelta(hours=24)).isoformat(),'views':1000}
    assert client.post('/api/v1/studio/research/observations',json=body,headers=headers).status_code==201
    first=client.get('/api/v1/studio/research').json()[0]
    assert first['views_per_hour'] is None and first['competition']=='unknown'
    body.update(observed_at=now.isoformat(),views=3400);headers['Idempotency-Key']=str(uuid4())
    assert client.post('/api/v1/studio/research/observations',json=body,headers=headers).status_code==201
    result=client.get('/api/v1/studio/research').json()[0]
    assert result['views_per_hour']==100 and result['confidence']=='UNVERIFIED'
    body.update(source_url='https://127.0.0.1/internal');headers['Idempotency-Key']=str(uuid4())
    assert client.post('/api/v1/studio/research/observations',json=body,headers=headers).status_code==422

@pytest.mark.media
def test_local_ocr_and_panel_proposals_preserve_originals(product):
    _,db,store=product;record=sample(db,store);jobs=RenderJobs(db)
    before=[p['original_asset_id'] for p in record['pages']]
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()),kind='analysis')
    assert run_once(db,store)
    record=Editorial(db).get(record['id'])
    assert record['analysis']['status']=='HUMAN_REVIEW_REQUIRED',jobs.list(record['id'])
    assert len(record['analysis']['pages'])==3
    assert [p['original_asset_id'] for p in record['pages']]==before
    assert record['pages'][0]['text']==STORY[0][1]
    assert record['analysis']['pages'][0]['panels']
    assert 'flamingo' in record['analysis']['pages'][0]['proposed_text'].lower()
    assert record['analysis']['status']=='HUMAN_REVIEW_REQUIRED'  # OCR did not recover all artwork text.


def test_edit_during_render_blocks_even_if_approval_was_revoked(product):
    _,db,store=product;record=approved(db,store);jobs=RenderJobs(db)
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()));job=jobs.claim()
    unchanged=EditInput.model_validate({'revision':record['revision'],'beats':record['beats'],'notes':'New editorial review required'})
    edited=Editorial(db).edit(record['id'],unchanged,str(uuid4()))
    assert edited['script_approval'] is None
    assert jobs.finish(job,result={'unused':'a stale output'})
    assert jobs.list(record['id'])[0]['state']=='failed'
    assert Editorial(db).get(record['id'])['export'] is None


def test_original_uploaded_bytes_are_preserved(product):
    _,db,store=product
    import base64,io
    from PIL import Image
    original=Image.new('RGB',(64,96),'red');buffer=io.BytesIO();original.save(buffer,format='JPEG',quality=80)
    data=buffer.getvalue();ing=Ingestion(db,store);series=ing.series(SeriesInput(title='Exact original byte fixture'),str(uuid4()))
    record=ing.import_source(SourceInput.model_validate({'series_id':series['id'],'chapter_key':'1','title':'JPEG input','rights':{'basis':'original','rightsholder':'Fixture','evidence':'Authored RGB fixture','allow_internal':True},'pages':[{'order':1,'filename':'original.jpg','data_base64':base64.b64encode(data).decode()}]}),str(uuid4()))
    page=record['pages'][0];assert page['original_asset_id']!=page['asset_id']
    assets=db.tables['media_assets']
    with db.engine.connect() as conn:asset=conn.execute(select(assets).where(assets.c.id==page['original_asset_id'])).mappings().one()
    assert store.read_blob(asset['object_key'],asset['sha256'])==data


def test_request_body_limit_catches_chunked_input():
    from fastapi import FastAPI,Request
    from flamingo_next_api.body_limit import BodyLimitMiddleware
    app=FastAPI()
    @app.post('/')
    async def read(request:Request):return {'bytes':len(await request.body())}
    app.add_middleware(BodyLimitMiddleware,max_bytes=64)
    with TestClient(app) as client:
        assert client.post('/',content=b'x'*63).status_code==200
        assert client.post('/',content=iter([b'x'*40,b'x'*40])).status_code==413


def test_canon_is_source_scoped_and_invalidates_affected_episodes(product):
    _,db,store=product
    from flamingo_next_api.canon import Canon
    from flamingo_next_api.product_models import CanonInput
    from fastapi import HTTPException
    record=approved(db,store);canon=Canon(db)
    body=CanonInput.model_validate({'revision':0,'confirmed_source_review':True,'character':{'name':'keeper','aliases':['The keeper'],'pronunciation':'keep-er','evidence_page_id':record['pages'][0]['id']},'fact':'The keeper carries a lantern.'})
    result=canon.approve(record['series_id'],body,str(uuid4()))
    assert record['id'] in result['invalidated_production_ids']
    current=Editorial(db).get(record['id'])
    assert current['script_approval'] is None and current['canon_revision']==1
    bible=canon.get(record['series_id']);assert bible['characters'][0]['canonical_name']=='keeper'
    assert bible['facts'][0]['value']['text']=='The keeper carries a lantern.'
    with pytest.raises(HTTPException):canon.approve(record['series_id'],body,str(uuid4()))
    other=sample(db,store)
    body.revision=1;body.character.evidence_page_id=UUID(other['pages'][0]['id'])
    with pytest.raises(HTTPException) as err:canon.approve(record['series_id'],body,str(uuid4()))
    assert err.value.status_code==422


def test_restore_creates_new_revision_preserving_source_and_package(product):
    _,db,store=product
    from flamingo_next_api.product_models import RestoreInput
    record=sample(db,store);editor=Editorial(db)
    original=copy.deepcopy(record)
    body=EditInput.model_validate({'revision':record['revision'],'beats':record['beats']})
    body.beats[0].spoken_text='A changed narration beat.'
    record=editor.edit(record['id'],body,str(uuid4()))
    restored=editor.restore_script(record['id'],RestoreInput(revision=record['revision'],restore_revision=original['revision']),str(uuid4()))
    assert restored['beats']==original['beats']
    assert restored['revision']>record['revision'] and restored['source_sha']==original['source_sha']
    assert restored['packaging']==record['packaging'] and restored['script_approval'] is None

@pytest.mark.media
def test_authenticated_media_cache_reuses_unchanged_voice_and_clips(product):
    _,db,store=product
    from flamingo_next_api.media_engine import MediaEngine
    record=approved(db,store);assets=db.tables['media_assets']
    with db.engine.connect() as conn:source_assets={str(r['id']):dict(r) for r in conn.execute(select(assets).where(assets.c.id.in_([p['asset_id'] for p in record['pages']]))).mappings()}
    engine=MediaEngine(store)
    first=engine.render(record,source_assets)
    second=engine.render(record,source_assets)
    assert second['export']['manifest']['voice_cache_hits']==3
    assert second['export']['manifest']['clip_cache_hits']==3
    assert second['export']['sha256']==first['export']['sha256']
    # An attacker-controlled cache index cannot point at arbitrary narration.
    identity='a'*64
    store.client.put_object(Bucket=store.settings.bucket,Key=f'voice-cache/{identity}.json',Body=b'{"input_sha":"forged","signature":"forged","blob":{}}')
    assert engine.read_cache('voice',identity) is None


def test_packaging_proposals_require_approval_and_preserve_owner_fields(product):
    _,db,store=product
    from flamingo_next_api.packaging import Packaging
    from fastapi import HTTPException
    service=Packaging(db,store);editor=Editorial(db);record=sample(db,store)
    with pytest.raises(HTTPException):service.propose(record['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    record=editor.approve_script(record['id'],ScriptApproval(revision=record['revision'],confirmed_source_review=True),str(uuid4()))
    record=editor.package(record['id'],PackageInput(revision=record['revision'],title='Locked owner promise',description='A distinct owner description.',tags=['original']),str(uuid4()))
    key=str(uuid4());body=RevisionInput(revision=record['revision'])
    concepts=service.propose(record['id'],body,key)
    assert len(concepts)==3 and service.propose(record['id'],body,key)==concepts
    assert editor.get(record['id'])['packaging']==record['packaging']
    assert all(p['source_page_id'] in [page['id'] for page in record['pages']] for p in concepts)
    chosen=service.apply(record['id'],concepts[0]['id'],body,str(uuid4()))
    assert chosen['packaging']['thumbnail_asset_id']==concepts[0]['asset_id']
    assert chosen['packaging']['description']==record['packaging']['description']
    assert chosen['packaging']['tags']==['original']
    saved=editor.package(record['id'],PackageInput(revision=chosen['revision'],title='Another owner title',description='Another description'),str(uuid4()))
    assert saved['packaging']['thumbnail_asset_id']==concepts[0]['asset_id']
    edit=EditInput.model_validate({'revision':saved['revision'],'beats':saved['beats']});edit.beats[0].spoken_text+=' Something changes.'
    changed=editor.edit(record['id'],edit,str(uuid4()))
    assert all(p['stale'] for p in service.list(record['id']))
    with pytest.raises(HTTPException):service.apply(record['id'],concepts[0]['id'],RevisionInput(revision=changed['revision']),str(uuid4()))


def test_media_subprocess_reads_large_output_and_bounds_it(product):
    _,_,store=product
    import sys
    from flamingo_next_api.media_engine import MediaEngine
    engine=MediaEngine(store)
    # Tesseract can emit more than a pipe buffer; waiting before draining must not deadlock.
    assert len(engine.run([sys.executable,'-c','import sys;sys.stdout.write("x"*2000000)'],timeout=5))==2_000_000
    with pytest.raises(RuntimeError,match='8 MB'):
        engine.run([sys.executable,'-c','import sys;sys.stdout.write("x"*8000001)'],timeout=5)

@pytest.mark.media
def test_panel_motion_and_tall_page_scroll_render_real_frames(product,tmp_path):
    _,_,store=product
    import io,hashlib
    from PIL import Image,ImageDraw
    from flamingo_next_api.media_engine import MediaEngine
    engine=MediaEngine(store)
    image=Image.new('RGB',(320,1200),'#305267');draw=ImageDraw.Draw(image)
    for y in range(0,1200,100):draw.rectangle((y%200,y,319,y+50),fill=(y//5%255,180,90))
    path=tmp_path/'tall.png';image.save(path)
    hashes=[]
    for motion in ('static','zoom_in','zoom_out','pan_left','pan_right','scroll_down'):
        output=tmp_path/f'{motion}.mp4'
        filters=engine.shot_filters({'crop':[0,0,1,1],'motion':motion},320,180,24)
        engine.run(['ffmpeg','-v','error','-y','-loop','1','-framerate','24','-i',str(path),'-vf',filters,'-frames:v','24','-an','-c:v','libx264',str(output)],timeout=10)
        probe=json.loads(engine.run(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
        assert int(probe['streams'][0]['nb_frames'])==24
        hashes.append(hashlib.sha256(output.read_bytes()).hexdigest())
    assert len(set(hashes))==6


def test_rights_revision_revokes_variants_and_fences_pending_render(product):
    _,db,store=product
    from flamingo_next_api.rights import Rights
    from flamingo_next_api.product_models import RightsRevisionInput
    from fastapi import HTTPException
    editor=Editorial(db);record=approved(db,store);jobs=RenderJobs(db)
    variant=editor.variant(record['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()));claim=jobs.claim()
    revoked=Rights(db).revise(record['id'],RightsRevisionInput.model_validate({'revision':record['revision'],'rights':record['rights']|{'basis':'unknown','allow_internal':False,'evidence':'Fixture permission revoked for regression test.'}}),str(uuid4()))
    assert revoked['rights_id']!=record['rights_id'] and revoked['source_sha']==record['source_sha']
    other=editor.get(variant['id']);assert other['rights_id']==revoked['rights_id'] and other['script_approval'] is None
    with pytest.raises(HTTPException) as err:editor.approve_script(other['id'],ScriptApproval(revision=other['revision'],confirmed_source_review=True),str(uuid4()))
    assert err.value.status_code==403
    assert jobs.finish(claim)
    assert jobs.list(record['id'])[0]['state']=='failed'
    with pytest.raises(HTTPException):jobs.enqueue(revoked['id'],RevisionInput(revision=revoked['revision']),str(uuid4()),kind='analysis')

@pytest.mark.media
def test_vertical_review_is_separate_and_edits_invalidate_both_exports(product):
    _,db,store=product
    editor=Editorial(db);record=approved(db,store);jobs=RenderJobs(db)
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()),kind='vertical');assert run_once(db,store)
    record=editor.get(record['id']);assert record['vertical_qa']['status']=='PASS'
    assert record['vertical_export']['width']==720 and record['vertical_export']['height']==1280
    record=editor.package(record['id'],PackageInput(revision=record['revision'],title='Original vertical story',description='A separate private vertical fixture.'),str(uuid4()))
    record=editor.review(record['id'],ReviewInput(revision=record['revision'],kind='vertical',confirmed_watched=True,confirmed_rights=True,decision='approve',notes='Automated fixture review; not owner creative acceptance.'),str(uuid4()))
    assert record['vertical_review']['decision']=='approve' and record['review'] is None
    edited=editor.edit(record['id'],EditInput.model_validate({'revision':record['revision'],'beats':record['beats']}),str(uuid4()))
    assert edited['vertical_review'] is None and edited['vertical_export'] is None and edited['export'] is None


def test_neural_voice_model_missing_or_modified_fails_closed_without_download(product,tmp_path,monkeypatch):
    _,_,store=product
    from flamingo_next_api import voice_models
    from flamingo_next_api.media_engine import MediaEngine
    monkeypatch.setenv('FNS_KOKORO_DIR',str(tmp_path))
    assert voice_models.installed() is False
    with pytest.raises(RuntimeError,match='invalid checksum'):voice_models.verify()
    # Model loading occurs in a supervised process; it cannot silently switch voices or fetch files.
    with pytest.raises(RuntimeError,match='absent or has an invalid checksum'):
        MediaEngine(store).speech('A distinct regression fixture without a cached voice.',tmp_path,0,'kokoro-am_michael-v1')
    assert not (tmp_path/'kokoro-v1.0.onnx').exists()

@pytest.mark.media
def test_critical_findings_survive_rerenders_and_explicit_variants_until_retest(product):
    _,db,store=product
    from flamingo_next_api.review_findings import Findings
    from flamingo_next_api.product_models import FindingInput,FindingResolution
    from fastapi import HTTPException
    record=approved(db,store);editor=Editorial(db);jobs=RenderJobs(db);findings=Findings(db)
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()));assert run_once(db,store)
    record=editor.get(record['id'])
    found=findings.add(record['id'],FindingInput(revision=record['revision'],beat_id=record['beats'][0]['id'],category='voice',severity='P1',description='Regression fixture: confirm the first narration beat after repair.'),str(uuid4()))
    item=findings.list(record['id'])[0];assert item['start_ms']==0 and item['page_id']==record['beats'][0]['page_id']
    record=editor.get(record['id']);record=editor.package(record['id'],PackageInput(revision=record['revision'],title='A source-backed promise',description='An original private recap fixture.'),str(uuid4()))
    with pytest.raises(HTTPException,match='critical quality findings'):
        editor.review(record['id'],ReviewInput(revision=record['revision'],confirmed_watched=True,confirmed_rights=True,decision='approve',notes='Must be blocked while the critical finding is open.'),str(uuid4()))
    variant=editor.variant(record['id'],RevisionInput(revision=record['revision']),str(uuid4()))
    assert len(findings.list(variant['id']))==1 and findings.list(variant['id'])[0]['status']=='open'
    with pytest.raises(HTTPException):findings.resolve(variant['id'],found['finding_id'],FindingResolution(revision=variant['revision'],confirmed_retest=True,notes='Cannot resolve a finding owned by another production.'),str(uuid4()))
    edit=EditInput.model_validate({'revision':record['revision'],'beats':record['beats']});edit.beats[0].spoken_text+=' The journey begins.'
    record=editor.edit(record['id'],edit,str(uuid4()))
    with pytest.raises(HTTPException):findings.resolve(record['id'],found['finding_id'],FindingResolution(revision=record['revision'],confirmed_retest=True,notes='No current export; repair cannot be confirmed yet.'),str(uuid4()))
    record=editor.approve_script(record['id'],ScriptApproval(revision=record['revision'],confirmed_source_review=True),str(uuid4()))
    jobs.enqueue(record['id'],RevisionInput(revision=record['revision']),str(uuid4()));assert run_once(db,store)
    record=editor.get(record['id']);assert findings.list(record['id'])[0]['status']=='open'
    record=findings.resolve(record['id'],found['finding_id'],FindingResolution(revision=record['revision'],confirmed_retest=True,notes='Automated fixture retest confirmation only; not owner acceptance.'),str(uuid4()))
    assert findings.list(record['id'])[0]['status']=='verified_fixed'
    record=editor.review(record['id'],ReviewInput(revision=record['revision'],confirmed_watched=True,confirmed_rights=True,decision='approve',notes='Automated fixture after a recorded retest; not owner acceptance.'),str(uuid4()))
    assert record['status']=='APPROVED_PRIVATE'
