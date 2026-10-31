"""Authenticated product routes; domain services own mutable behavior."""
import json
import time
from uuid import UUID
from fastapi import APIRouter,Depends,Header,HTTPException,Request,Response
from sqlalchemy import select
from .security import require_owner
from .product_db import ProductDB,OWNER
from .product_models import (SeriesInput,SourceInput,EditInput,RevisionInput,ScriptApproval,PackageInput,ReviewInput,ResearchInput,MetricInput,RestoreInput,CanonInput,RightsRevisionInput,FindingInput,FindingResolution)
from .ingestion import Ingestion
from .editorial import Editorial,approval_fingerprint,input_fingerprint
from .render_jobs import RenderJobs
from .insights import Insights

router=APIRouter(prefix='/api/v1/studio',dependencies=[Depends(require_owner)])

def db(request):return request.app.state.product

def ingestion(request):return Ingestion(db(request),request.app.state.storage)

def asset_link(request,asset_id,owner):
    table=db(request).tables['media_assets']
    with db(request).engine.connect() as conn:
        asset=conn.execute(select(table).where(table.c.id==asset_id,table.c.bucket==request.app.state.settings.bucket)).mappings().first()
    if not asset:raise HTTPException(404,'Unknown media asset')
    expires=int(time.time())+300
    signature=request.app.state.storage.signature(asset['sha256'],owner['id'],expires)
    return dict(asset)|{'url':f'/api/v1/studio/assets/{asset_id}/content?expires={expires}&signature={signature}'}

@router.get('/series')
def series(request:Request):return ingestion(request).list_series()

@router.post('/series',status_code=201)
def create_series(body:SeriesInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return ingestion(request).series(body,idempotency_key)

@router.get('/episodes')
def episodes(request:Request):return Editorial(db(request)).list()

@router.post('/sources',status_code=201)
def source(body:SourceInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return ingestion(request).import_source(body,idempotency_key)

@router.get('/episodes/{pid}')
def episode(pid:UUID,request:Request):return Editorial(db(request)).get(pid)

@router.get('/episodes/{pid}/history')
def history(pid:UUID,request:Request):return Editorial(db(request)).snapshots(pid)

@router.put('/episodes/{pid}/script')
def script(pid:UUID,body:EditInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).edit(pid,body,idempotency_key)

@router.post('/episodes/{pid}/approve-script')
def approve_script(pid:UUID,body:ScriptApproval,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).approve_script(pid,body,idempotency_key)

@router.put('/episodes/{pid}/package')
def package(pid:UUID,body:PackageInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).package(pid,body,idempotency_key)

@router.post('/episodes/{pid}/review')
def review(pid:UUID,body:ReviewInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).review(pid,body,idempotency_key)

@router.post('/episodes/{pid}/variant',status_code=201)
def variant(pid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).variant(pid,body,idempotency_key)

@router.get('/episodes/{pid}/render-jobs')
def render_jobs(pid:UUID,request:Request):return RenderJobs(db(request)).list(pid)

@router.post('/episodes/{pid}/render',status_code=202)
def render(pid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return RenderJobs(db(request)).enqueue(pid,body,idempotency_key)

@router.post('/episodes/{pid}/render-vertical',status_code=202)
def vertical(pid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return RenderJobs(db(request)).enqueue(pid,body,idempotency_key,kind='vertical')

@router.post('/render-jobs/{jid}/cancel')
def cancel(jid:UUID,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return RenderJobs(db(request)).cancel(jid,idempotency_key)

@router.get('/assets/{asset_id}/signed-url')
def signed_asset(asset_id:UUID,request:Request,owner=Depends(require_owner)):
    return asset_link(request,asset_id,owner)

@router.get('/assets/{asset_id}/content')
def content(asset_id:UUID,request:Request,expires:int,signature:str,owner=Depends(require_owner)):
    asset=asset_link(request,asset_id,owner)
    storage=request.app.state.storage
    storage.verify(asset['sha256'],owner['id'],expires,signature)
    data=storage.read_blob(asset['object_key'],asset['sha256'])
    headers={'Accept-Ranges':'bytes','Content-Security-Policy':"default-src 'none'; sandbox"}
    range_header=request.headers.get('range')
    if range_header:
        import re
        match=re.fullmatch(r'bytes=(\d+)-(\d*)',range_header)
        if not match:raise HTTPException(416,'Unsupported media range')
        start=int(match.group(1));end=min(int(match.group(2)) if match.group(2) else len(data)-1,len(data)-1)
        if start>end or start>=len(data):raise HTTPException(416,'Media range out of bounds')
        headers['Content-Range']=f'bytes {start}-{end}/{len(data)}'
        return Response(data[start:end+1],status_code=206,media_type=asset['mime_type'],headers=headers)
    return Response(data,media_type=asset['mime_type'],headers=headers)

@router.get('/episodes/{pid}/export-url')
def export_url(pid:UUID,request:Request,owner=Depends(require_owner),kind:str='longform',asset:str='video'):
    record=Editorial(db(request)).get(pid)
    export=record.get('vertical_export' if kind=='vertical' else 'export')
    if not export:raise HTTPException(409,'No current export exists')
    if export['manifest'].get('input_sha')!=input_fingerprint(record):raise HTTPException(409,'This export belongs to an older input version. Approve and render the current script.')
    if asset not in ('video','manifest','voice','captions'):raise HTTPException(422,'Unknown export artifact')
    blob=export if asset=='video' else export[{'manifest':'manifest_blob','voice':'voice_blob','captions':'captions_blob'}[asset]]
    mime={'video':'video/mp4','manifest':'application/json','voice':'audio/wav','captions':'text/vtt'}[asset]
    table=db(request).tables['media_assets']
    with db(request).engine.connect() as conn:
        aid=conn.execute(select(table.c.id).where(table.c.bucket==request.app.state.settings.bucket,table.c.object_key==blob['key'])).scalar_one_or_none()
    if not aid:raise HTTPException(409,'Export asset registration is incomplete')
    return asset_link(request,aid,owner)

@router.get('/research')
def research(request:Request):return Insights(db(request)).research()

@router.post('/research/observations',status_code=201)
def observation(body:ResearchInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Insights(db(request)).add_observation(body,idempotency_key)

@router.get('/analytics')
def analytics(request:Request):return Insights(db(request)).analytics()

@router.post('/analytics',status_code=201)
def metric(body:MetricInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Insights(db(request)).add_metric(body,idempotency_key)

@router.get('/publishing')
def publishing(request:Request):
    items=Editorial(db(request)).list()
    return {'enabled':False,'destination_connected':False,'items':[{'id':r['id'],'title':r['title'],'status':r['status'],'rights_distribution':r['rights']['allow_distribution'],'approval_current':bool(r['review'] and r['review']['decision']=='approve' and r['review']['fingerprint']==approval_fingerprint(r)),'export_sha':r['export']['sha256'] if r['export'] else None} for r in items if r['export']]}

@router.post('/episodes/{pid}/publish')
def publish(pid:UUID,request:Request):
    raise HTTPException(403,'Publishing is disabled. A separately authorized destination, rights and exact release approval are required.')

@router.post('/demo-episode',status_code=201)
def demo(request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .demo_episode import create_demo
    # Internal calls use separate idempotency receipts; avoid nested transactions.
    return create_demo(ingestion(request),Editorial(db(request)),idempotency_key)

@router.get('/render-jobs')
def all_render_jobs(request:Request):
    service=RenderJobs(db(request));table=db(request).tables['studio_render_jobs']
    with db(request).engine.connect() as conn:
        return [service.public(r) for r in conn.execute(select(table).order_by(table.c.created_at.desc()).limit(200)).mappings()]


@router.post('/render-jobs/{jid}/retry')
def retry_render(jid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return RenderJobs(db(request)).retry(jid,body,idempotency_key)


@router.post('/episodes/{pid}/analyze-source',status_code=202)
def analyze_source(pid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return RenderJobs(db(request)).enqueue(pid,body,idempotency_key,kind='analysis')


@router.post('/episodes/{pid}/restore-script')
def restore_script(pid:UUID,body:RestoreInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    return Editorial(db(request)).restore_script(pid,body,idempotency_key)


@router.get('/series/{wid}/bible')
def series_bible(wid:UUID,request:Request):
    from .canon import Canon
    return Canon(db(request)).get(wid)

@router.post('/series/{wid}/bible/approve')
def approve_canon(wid:UUID,body:CanonInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .canon import Canon
    return Canon(db(request)).approve(wid,body,idempotency_key)

@router.get('/episodes/{pid}/packaging-proposals')
def packaging_proposals(pid:UUID,request:Request):
    from .packaging import Packaging
    return Packaging(db(request),request.app.state.storage).list(pid)

@router.post('/episodes/{pid}/packaging-proposals',status_code=201)
def propose_package(pid:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .packaging import Packaging
    return Packaging(db(request),request.app.state.storage).propose(pid,body,idempotency_key)

@router.post('/episodes/{pid}/packaging-proposals/{candidate_id}/apply')
def apply_package(pid:UUID,candidate_id:UUID,body:RevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .packaging import Packaging
    return Packaging(db(request),request.app.state.storage).apply(pid,candidate_id,body,idempotency_key)

@router.put('/episodes/{pid}/rights')
def update_rights(pid:UUID,body:RightsRevisionInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .rights import Rights
    return Rights(db(request)).revise(pid,body,idempotency_key)

@router.get('/episodes/{pid}/findings')
def quality_findings(pid:UUID,request:Request):
    from .review_findings import Findings
    return Findings(db(request)).list(pid)

@router.post('/episodes/{pid}/findings',status_code=201)
def add_finding(pid:UUID,body:FindingInput,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .review_findings import Findings
    return Findings(db(request)).add(pid,body,idempotency_key)

@router.post('/episodes/{pid}/findings/{finding_id}/resolve')
def resolve_finding(pid:UUID,finding_id:UUID,body:FindingResolution,request:Request,idempotency_key:str=Header(min_length=8,max_length=160)):
    from .review_findings import Findings
    return Findings(db(request)).resolve(pid,finding_id,body,idempotency_key)
