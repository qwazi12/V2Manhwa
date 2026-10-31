"""Durable bounded render claims with heartbeat and exact-input fencing."""
import time
import secrets
from uuid import uuid4
from sqlalchemy import select,or_,and_,update,text
from fastapi import HTTPException
from .editorial import input_fingerprint,require_internal_rights

class RenderJobs:
    def __init__(self,db): self.db=db
    def enqueue(self,pid,body,key,kind='longform'):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            require_internal_rights(record)
            fingerprint=record['source_sha'] if kind=='analysis' else input_fingerprint(record)
            if kind!='analysis' and (not record['script_approval'] or record['script_approval']['input_sha']!=fingerprint):
                raise HTTPException(409,'Approve the current source-linked script first')
            table=self.db.tables['studio_render_jobs']
            old=conn.execute(select(table).where(table.c.production_id==pid,table.c.input_sha==fingerprint,table.c.kind==kind)).mappings().first()
            if old:
                if old['state']=='completed' and old['result'] and kind in ('longform','vertical'):
                    export_key='vertical_export' if kind=='vertical' else 'export'
                    if not record.get(export_key):
                        if kind=='longform':record.update(export=old['result']['export'],qa=old['result']['qa'],review=None,status='MEDIA_REVIEW')
                        else:record.update(vertical_export=old['result']['export'],vertical_qa=old['result']['qa'],vertical_review=None)
                        self.db.save(conn,record,'verified_export_reused')
                return self.public(old)
            jid=uuid4()
            conn.execute(table.insert().values(id=jid,production_id=pid,input_revision=record['revision'],input_sha=fingerprint,kind=kind,state='queued',idempotency_key=key))
            self.db.audit(conn,'render_queued',pid,{'revision':record['revision']})
            return self.public(conn.execute(select(table).where(table.c.id==jid)).mappings().one())
        return self.db.command('render:'+str(pid)+':'+kind,key,body.model_dump(mode='json'),execute)
    def public(self,row): return {k:v for k,v in dict(row).items() if k not in ('lease_token','lease_until','idempotency_key')}
    def list(self,pid):
        table=self.db.tables['studio_render_jobs']
        with self.db.engine.connect() as conn:
            return [self.public(r) for r in conn.execute(select(table).where(table.c.production_id==pid).order_by(table.c.created_at.desc())).mappings()]
    def claim(self):
        table=self.db.tables['studio_render_jobs']
        with self.db.engine.begin() as conn:
            row=conn.execute(select(table).where(or_(table.c.state=='queued',and_(table.c.state=='running',table.c.lease_until<time.time()))).order_by(table.c.created_at).limit(1).with_for_update(skip_locked=True)).mappings().first()
            if not row:return None
            if row['attempt']>=3:
                conn.execute(table.update().where(table.c.id==row['id']).values(state='failed',error='Worker recovery limit reached'));return None
            token=secrets.token_hex(24)
            conn.execute(table.update().where(table.c.id==row['id']).values(state='running',lease_token=token,lease_until=time.time()+40,attempt=row['attempt']+1))
            return dict(row)|{'lease_token':token}
    def heartbeat(self,jid,token):
        table=self.db.tables['studio_render_jobs']
        with self.db.engine.begin() as conn:
            return bool(conn.execute(table.update().where(table.c.id==jid,table.c.state=='running',table.c.lease_token==token,table.c.cancel_requested==False,table.c.lease_until>time.time()).values(lease_until=time.time()+40)).rowcount)
    def cancel(self,jid,key):
        def execute(conn):
            table=self.db.tables['studio_render_jobs']
            row=conn.execute(select(table).where(table.c.id==jid).with_for_update()).mappings().first()
            if not row:raise HTTPException(404,'Unknown render job')
            if row['state'] not in ('queued','running'):raise HTTPException(409,'Render has already stopped')
            conn.execute(table.update().where(table.c.id==jid).values(state='cancelled',cancel_requested=True,lease_token=None,lease_until=None))
            self.db.audit(conn,'render_cancelled',row['production_id'])
            return {'id':str(jid),'state':'cancelled'}
        return self.db.command('render_cancel',key,{'id':str(jid)},execute)
    def finish(self,job,result=None,error=None):
        table=self.db.tables['studio_render_jobs']
        with self.db.engine.begin() as conn:
            row=conn.execute(select(table).where(table.c.id==job['id']).with_for_update()).mappings().one()
            if row['state']!='running' or row['lease_token']!=job['lease_token'] or row['lease_until']<=time.time():return False
            record=self.db.load(conn,row['production_id'],True)
            try:require_internal_rights(record)
            except HTTPException:error='Internal source permission was revoked or expired during this job'
            if job['kind']=='analysis':
                if record['source_sha']!=job['input_sha']:error='Source revision changed during analysis'
                if not error:
                    record['analysis']=result
                    self.db.save(conn,record,'local_source_analysis_completed')
                conn.execute(table.update().where(table.c.id==job['id']).values(state='failed' if error else 'completed',result=result,error=error,lease_token=None,lease_until=None))
                return True
            if input_fingerprint(record)!=job['input_sha'] or not record['script_approval'] or record['script_approval']['input_sha']!=job['input_sha']:
                error='Script changed while rendering. The output is stale.'
            if not error:
                from sqlalchemy.dialects.postgresql import insert
                assets=self.db.tables['media_assets']
                for blob,stage in ((result['export'],'final'),(result['export']['manifest_blob'],'intermediate'),(result['export']['voice_blob'],'intermediate'),(result['export']['captions_blob'],'intermediate')):
                    conn.execute(insert(assets).values(id=uuid4(),bucket=result['bucket'],object_key=blob['key'],sha256=blob['sha256'],size_bytes=blob['size_bytes'],mime_type=blob['mime_type'],stage=stage,rights_scope='internal-authorized').on_conflict_do_nothing(index_elements=['bucket','object_key']))
                if job['kind']=='longform':
                    record.update(export=result['export'],qa=result['qa'],review=None,status='MEDIA_REVIEW')
                    self.db.save(conn,record,'render_completed')
                else:
                    record['vertical_export']=result['export'];record['vertical_qa']=result['qa'];record['vertical_review']=None
                    self.db.save(conn,record,'vertical_render_completed')
            conn.execute(table.update().where(table.c.id==job['id']).values(state='failed' if error else 'completed',result=result,error=error,lease_token=None,lease_until=None))
            return True

    def retry(self,jid,body,key):
        def execute(conn):
            table=self.db.tables['studio_render_jobs']
            row=conn.execute(select(table).where(table.c.id==jid).with_for_update()).mappings().first()
            if not row:raise HTTPException(404,'Unknown render job')
            record=self.db.load(conn,row['production_id'],True);self.db.require_revision(record,body.revision)
            if row['state'] not in ('failed','cancelled') or row['attempt']>=3:
                raise HTTPException(409,'Only stopped jobs below the recovery limit can be retried')
            require_internal_rights(record)
            if row['kind']!='analysis' and (not record['script_approval'] or record['script_approval']['input_sha']!=row['input_sha'] or input_fingerprint(record)!=row['input_sha']):
                raise HTTPException(409,'This job is stale. Approve and render the current script instead.')
            conn.execute(table.update().where(table.c.id==jid).values(state='queued',cancel_requested=False,error=None,lease_token=None,lease_until=None))
            self.db.audit(conn,'render_retry_requested',row['production_id'])
            return {'id':str(jid),'state':'queued'}
        return self.db.command('render_retry:'+str(jid),key,body.model_dump(mode='json'),execute)
