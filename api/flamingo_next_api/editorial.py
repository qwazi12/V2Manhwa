"""Versioned source-linked editorial state and exact-input approval gates."""
from copy import deepcopy
from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import select,func,update,text
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException
from .product_db import ProductDB,sha,OWNER


def editorial_checks(record):
    beats=record['beats']; pages={p['id'] for p in record['pages'] if p['kind']=='story'}
    covered={b['page_id'] for b in beats}
    return {'source_pages':len(pages),'covered_pages':len(pages & covered),
        'uncovered_page_ids':sorted(pages-covered),'has_script':bool(beats),
        'semantic_verdict':'HUMAN_REVIEW_REQUIRED','provider':'manual-editorial'}

def input_fingerprint(record):
    return sha({'source_sha':record['source_sha'],'beats':record['beats'],'voice':record['voice'],'canon_revision':record.get('canon_revision',0),'pronunciations':record.get('pronunciations',{})})

def require_internal_rights(record):
    rights=record['rights'];expiry=rights.get('expires_at')
    if rights['basis']=='unknown' or not rights['allow_internal'] or (expiry and datetime.fromisoformat(expiry)<=datetime.now(timezone.utc)):
        raise HTTPException(403,'Valid internal-use rights are required for this action')

def approval_fingerprint(record,kind='longform'):
    return sha({'source':record['source_sha'],'script':input_fingerprint(record),'kind':kind,'export':record.get('vertical_export' if kind=='vertical' else 'export'),
        'qa':record.get('vertical_qa' if kind=='vertical' else 'qa'),'package':record['packaging'],'rights':record['rights']})

class Editorial:
    def __init__(self,db:ProductDB): self.db=db
    def list(self):
        t=self.db.tables['studio_episodes']
        with self.db.engine.connect() as conn:
            return [r['payload'] for r in conn.execute(select(t).order_by(t.c.updated_at.desc()).limit(200)).mappings()]
    def get(self,pid):
        with self.db.engine.connect() as conn: return self.db.load(conn,pid)
    def snapshots(self,pid):
        t=self.db.tables['studio_snapshots']
        with self.db.engine.connect() as conn:
            return [dict(r) for r in conn.execute(select(t.c.revision,t.c.sha256,t.c.created_at).where(t.c.production_id==pid).order_by(t.c.revision.desc())).mappings()]
    def edit(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            ids={p['id'] for p in record['pages']}
            beats=[b.model_dump(mode='json') for b in body.beats]
            if len({b['id'] for b in beats})!=len(beats): raise HTTPException(422,'Beat IDs must be unique')
            if any(b['page_id'] not in ids for b in beats): raise HTTPException(422,'Each beat must link to this exact source revision')
            record.update(beats=beats,voice=body.voice,notes=body.notes,script_approval=None,export=None,vertical_export=None,vertical_qa=None,vertical_review=None,qa=None,review=None,status='SCRIPT_REVIEW')
            record['checks']=editorial_checks(record)
            return self.db.save(conn,record,'script_edited')
        return self.db.command('script_edit:'+str(pid),key,body.model_dump(mode='json'),execute)
    def approve_script(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            require_internal_rights(record)
            checks=editorial_checks(record)
            if not checks['has_script'] or checks['uncovered_page_ids']:
                raise HTTPException(409,'Every story page must be represented by a source-linked beat before approval')
            record['script_approval']={'input_sha':input_fingerprint(record),'reviewer':'local-owner','reviewed_at':datetime.now(timezone.utc).isoformat(),'coverage':checks}
            record['status']='READY_TO_RENDER'
            return self.db.save(conn,record,'script_approved')
        return self.db.command('script_approve:'+str(pid),key,body.model_dump(mode='json'),execute)
    def package(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            record['packaging']=record['packaging']|body.model_dump(exclude={'revision'})
            record['review']=None;record['vertical_review']=None
            return self.db.save(conn,record,'package_edited')
        return self.db.command('package_edit:'+str(pid),key,body.model_dump(mode='json'),execute)
    def review(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            export=record.get('vertical_export' if body.kind=='vertical' else 'export');qa=record.get('vertical_qa' if body.kind=='vertical' else 'qa')
            if not export or not qa or qa['status']!='PASS':
                raise HTTPException(409,'An exact, technically verified final export is required')
            if export['manifest'].get('input_sha')!=input_fingerprint(record) or not record['script_approval'] or record['script_approval']['input_sha']!=input_fingerprint(record):
                raise HTTPException(409,'This export is stale. Approve and render the current source/script/canon inputs.')
            if not record['packaging']['description']:
                raise HTTPException(409,'Finish the episode-specific package before review')
            require_internal_rights(record)
            if body.decision=='approve':
                from .review_findings import require_no_critical_findings
                require_no_critical_findings(self.db,conn,pid,body.kind)
            record['vertical_review' if body.kind=='vertical' else 'review']={'fingerprint':approval_fingerprint(record,body.kind),'decision':body.decision,'notes':body.notes,'reviewed_at':datetime.now(timezone.utc).isoformat(),'reviewer':'local-owner'}
            if body.kind=='longform':record['status']='APPROVED_PRIVATE' if body.decision=='approve' else 'NEEDS_CHANGES'
            if body.decision=='approve':
                # Permanent local made ledger. No remote channel/account is inferred.
                claims=self.db.tables['autopilot_claims']; channels=self.db.tables['channels']
                channel_id=conn.execute(select(channels.c.id).where(channels.c.platform=='local-private',channels.c.provider_channel_id=='private-library')).scalar()
                if not channel_id:
                    channel_id=uuid4();conn.execute(channels.insert().values(id=channel_id,platform='local-private',provider_channel_id='private-library',display_name='Local private library',status='disconnected'))
                ledger=self.db.tables['content_ledger']
                conn.execute(insert(ledger).values(work_id=record['series_id'],chapter_key=record['chapter_key'],channel_id=channel_id,content_type='short' if body.kind=='vertical' else 'longform_episode',first_production_id=pid,completed_at=func.now()).on_conflict_do_nothing())
            return self.db.save(conn,record,'private_export_reviewed')
        return self.db.command('review:'+str(pid),key,body.model_dump(mode='json'),execute)
    def variant(self,pid,body,key):
        def execute(conn):
            original=self.db.load(conn,pid,True);self.db.require_revision(original,body.revision)
            record=deepcopy(original);new_id=str(uuid4())
            record.update(id=new_id,revision=1,finding_resolutions=[],script_approval=None,export=None,vertical_export=None,vertical_qa=None,vertical_review=None,qa=None,review=None,status='SCRIPT_REVIEW',variant_of=str(pid))
            conn.execute(self.db.tables['productions'].insert().values(id=new_id,work_id=record['series_id'],format='single',variant_of=pid,owner_requested_remake=True,is_qa_only=False,status='SCRIPT_REVIEW',rights_manifest_id=record['rights_id'],created_by=OWNER))
            conn.execute(self.db.tables['production_episodes'].insert().values(production_id=new_id,episode_id=record['episode_id'],ordinal=1))
            from .review_findings import inherit_open_findings
            inherit_open_findings(self.db,conn,pid,new_id)
            return self.db.save(conn,record,'owner_variant_created',new=True)
        return self.db.command('variant:'+str(pid),key,body.model_dump(mode='json'),execute)

    def restore_script(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            snapshots=self.db.tables['studio_snapshots']
            previous=conn.execute(select(snapshots.c.payload).where(snapshots.c.production_id==pid,snapshots.c.revision==body.restore_revision)).scalar_one_or_none()
            if not previous:raise HTTPException(404,'Unknown historical revision')
            if previous['source_sha']!=record['source_sha']:raise HTTPException(409,'A script can only be restored against its exact source revision')
            record.update(beats=deepcopy(previous['beats']),notes=previous['notes'],voice=previous['voice'],script_approval=None,export=None,vertical_export=None,vertical_qa=None,vertical_review=None,qa=None,review=None,status='SCRIPT_REVIEW')
            return self.db.save(conn,record,'script_restored_from_revision')
        return self.db.command('restore_script:'+str(pid),key,body.model_dump(mode='json'),execute)
