"""Append-only rights revisions propagate to productions sharing a declaration."""
from uuid import uuid4
from sqlalchemy import select,text,func
from fastapi import HTTPException
from .product_db import OWNER

class Rights:
    def __init__(self,db):self.db=db
    def revise(self,pid,body,key):
        def execute(conn):
            initial=self.db.load(conn,pid);old_id=initial['rights_id']
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key,0))'),{'key':'rights:'+old_id})
            table=self.db.tables['studio_episodes']
            records=list(conn.execute(select(table).where(table.c.payload['rights_id'].astext==old_id).order_by(table.c.production_id).with_for_update()).mappings())
            current=next((row for row in records if str(row['production_id'])==str(pid)),None)
            if current is None:raise HTTPException(409,'Rights changed; refresh before editing')
            self.db.require_revision(current['payload'],body.revision)
            rights=self.db.tables['rights_manifests'];old=conn.execute(select(rights).where(rights.c.id==old_id)).mappings().one()
            new_id=uuid4()
            conn.execute(rights.insert().values(id=new_id,revision=old['revision']+1,basis=body.rights.basis,rightsholder=body.rights.rightsholder,allowed_actions={'internal':body.rights.allow_internal,'distribution':body.rights.allow_distribution},reviewer_id=OWNER,reviewed_at=func.now(),expires_at=body.rights.expires_at,notes=body.rights.evidence))
            result=None
            for row in records:
                record=dict(row['payload'])
                record.update(rights_id=str(new_id),rights=body.rights.model_dump(mode='json'),script_approval=None,export=None,vertical_export=None,qa=None,vertical_qa=None,review=None,vertical_review=None,status='SOURCE_REVIEW')
                conn.execute(self.db.tables['productions'].update().where(self.db.tables['productions'].c.id==row['production_id']).values(rights_manifest_id=new_id))
                saved=self.db.save(conn,record,'rights_revised_and_approvals_invalidated')
                if str(row['production_id'])==str(pid):result=saved
            return result
        return self.db.command('rights_revise:'+str(pid),key,body.model_dump(mode='json'),execute)
