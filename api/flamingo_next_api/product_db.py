"""Reflected product tables and transactional audit/snapshot helpers."""
import hashlib
import json
from uuid import uuid4, UUID
from functools import cached_property
from sqlalchemy import MetaData, select, text
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException

OWNER = UUID('eafde1ac-07af-4dc2-ae85-761411558498')

def dump(value):
    return json.dumps(value,sort_keys=True,default=str,separators=(',',':'))

def sha(value):
    return hashlib.sha256(dump(value).encode()).hexdigest()

class ProductDB:
    def __init__(self,engine): self.engine=engine
    @cached_property
    def tables(self):
        metadata=MetaData()
        metadata.reflect(bind=self.engine)
        return metadata.tables
    def owner(self,conn):
        table=self.tables['app_users']
        conn.execute(insert(table).values(id=OWNER,oidc_subject='local-owner',email='owner@local.invalid',display_name='Local studio owner',role='owner').on_conflict_do_nothing())
    def audit(self,conn,action,entity_id,after=None):
        self.owner(conn)
        conn.execute(self.tables['audit_events'].insert().values(actor_id=OWNER,action=action,entity_type='production',entity_id=entity_id,after_hash=sha(after) if after is not None else None,context={'mode':'local'}))
        conn.execute(self.tables['outbox_events'].insert().values(event_type=action,entity_id=entity_id,payload={'actor_id':str(OWNER),'revision':after.get('revision') if isinstance(after,dict) else None}))
    def load(self,conn,production_id,lock=False):
        table=self.tables['studio_episodes']
        query=select(table).where(table.c.production_id==production_id)
        if lock: query=query.with_for_update()
        row=conn.execute(query).mappings().first()
        if not row: raise HTTPException(404,'Unknown episode production')
        return dict(row['payload']) | {'id':str(row['production_id']),'revision':row['revision']}
    def require_revision(self,record,revision):
        if record['revision']!=revision: raise HTTPException(409,'This episode changed. Refresh before saving.')
    def save(self,conn,record,action,new=False):
        table=self.tables['studio_episodes']
        if new:
            conn.execute(table.insert().values(production_id=record['id'],revision=record['revision'],payload=record))
        else:
            record['revision']+=1
            conn.execute(table.update().where(table.c.production_id==record['id']).values(revision=record['revision'],payload=record,updated_at=text('now()')))
        conn.execute(self.tables['studio_snapshots'].insert().values(production_id=record['id'],revision=record['revision'],payload=record,sha256=sha(record)))
        self.audit(conn,action,record['id'],record)
        return record
    def command(self,action,key,payload,fn):
        if not key or not 8 <= len(key) <= 160: raise HTTPException(422,'An idempotency key of 8..160 characters is required')
        digest=sha(payload)
        with self.engine.begin() as conn:
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key,0))'),{'key':key})
            receipts=self.tables['studio_commands']
            old=conn.execute(select(receipts).where(receipts.c.idempotency_key==key)).mappings().first()
            if old:
                if old['action']!=action or old['input_sha']!=digest: raise HTTPException(409,'Idempotency key conflicts with another mutation')
                return old['result']
            result=fn(conn)
            # Normalize UUID/date objects before recording the exact response.
            result=json.loads(dump(result))
            conn.execute(receipts.insert().values(idempotency_key=key,action=action,input_sha=digest,result=result))
            return result
