"""Transactional job lifecycle, audit outbox and budget reservations."""
import hashlib
import json
import secrets
import time
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update, func, or_, and_, text
from sqlalchemy.dialects.postgresql import insert
from .database import jobs, events, reservations

def event(conn, job_id, kind, detail=None):
    conn.execute(events.insert().values(id=str(uuid4()), job_id=job_id, kind=kind, detail=detail or {}))

def record(conn, row):
    result = dict(row)
    for private in ('lease_token', 'lease_until', 'idempotency_key', 'input_hash'):
        result.pop(private, None)
    result['events'] = [dict(e) for e in conn.execute(select(events).where(events.c.job_id == row['id']).order_by(events.c.created_at, events.c.id)).mappings()]
    result['budget'] = dict(conn.execute(select(reservations).where(reservations.c.job_id == row['id'])).mappings().one())
    return result

class Repository:
    def __init__(self, engine):
        self.engine = engine

    def create(self, title, key):
        digest = hashlib.sha256(json.dumps({'title': title, 'source_kind': 'synthetic'}, sort_keys=True).encode()).hexdigest()
        with self.engine.begin() as conn:
            # Serializes daily reservation and same-key duplicate checks together.
            conn.execute(text('SELECT pg_advisory_xact_lock(246819)'))
            previous = conn.execute(select(jobs).where(jobs.c.idempotency_key == key)).mappings().first()
            if previous:
                if previous['input_hash'] != digest:
                    raise HTTPException(409, 'Idempotency key belongs to another request')
                return record(conn, previous)
            used = conn.execute(select(func.coalesce(func.sum(reservations.c.reserved_units), 0)).select_from(
                reservations.join(jobs)).where(jobs.c.created_at >= func.date_trunc('day', func.now()))).scalar_one()
            if used + 2 > 100:
                raise HTTPException(409, 'Daily mock budget is exhausted (100 units)')
            job_id = str(uuid4())
            conn.execute(jobs.insert().values(id=job_id, title=title, state='QUEUED', revision=1,
                input_hash=digest, idempotency_key=key, attempt=0))
            conn.execute(reservations.insert().values(job_id=job_id, reserved_units=2))
            event(conn, job_id, 'queued', {'source_kind':'synthetic', 'rights':'original fixture; internal preview'})
            return record(conn, conn.execute(select(jobs).where(jobs.c.id == job_id)).mappings().one())

    def list(self):
        with self.engine.begin() as conn:
            return [record(conn, r) for r in conn.execute(select(jobs).order_by(jobs.c.created_at.desc()).limit(100)).mappings()]

    def get(self, job_id):
        with self.engine.begin() as conn:
            row = conn.execute(select(jobs).where(jobs.c.id == job_id)).mappings().first()
            if not row:
                raise HTTPException(404, 'Unknown synthetic job')
            return record(conn, row)

    def cancel(self, job_id, revision):
        with self.engine.begin() as conn:
            row = conn.execute(select(jobs).where(jobs.c.id == job_id).with_for_update()).mappings().first()
            if not row:
                raise HTTPException(404, 'Unknown job')
            if row['revision'] != revision:
                raise HTTPException(409, 'Job changed. Refresh before cancelling.')
            if row['state'] not in ('QUEUED', 'RUNNING'):
                raise HTTPException(409, 'Only queued or running jobs can be cancelled')
            conn.execute(update(jobs).where(jobs.c.id == job_id).values(state='CANCELLED', revision=revision+1,
                lease_token=None, lease_until=None))
            conn.execute(update(reservations).where(reservations.c.job_id == job_id).values(settled_units=0))
            event(conn, job_id, 'cancelled')
        return self.get(job_id)

    def claim(self, lease_seconds=30):
        with self.engine.begin() as conn:
            row = conn.execute(select(jobs).where(or_(jobs.c.state == 'QUEUED', and_(
                jobs.c.state == 'RUNNING', jobs.c.lease_until < time.time()))).order_by(jobs.c.created_at)
                .with_for_update(skip_locked=True).limit(1)).mappings().first()
            if row is None:
                return None
            if row['attempt'] >= 3:
                conn.execute(update(jobs).where(jobs.c.id == row['id']).values(state='FAILED', error='Worker recovery limit reached', revision=row['revision']+1, lease_token=None, lease_until=None))
                conn.execute(update(reservations).where(reservations.c.job_id == row['id']).values(settled_units=0))
                event(conn, row['id'], 'failed', {'reason':'recovery_limit'})
                return None
            token = secrets.token_hex(24)
            values = dict(state='RUNNING', lease_token=token, lease_until=time.time()+lease_seconds,
                attempt=row['attempt']+1, revision=row['revision']+1)
            conn.execute(update(jobs).where(jobs.c.id == row['id']).values(**values))
            event(conn, row['id'], 'worker_claimed', {'attempt':values['attempt']})
            result = dict(row) | values
            result['budget'] = dict(conn.execute(select(reservations).where(reservations.c.job_id == row['id'])).mappings().one())
            return result

    def finish(self, job_id, token, digest=None, result=None, error=None):
        with self.engine.begin() as conn:
            row = conn.execute(select(jobs).where(jobs.c.id == job_id).with_for_update()).mappings().one()
            if row['state'] != 'RUNNING' or row['lease_token'] != token or row['lease_until'] <= time.time():
                return False  # Cancelled, expired or superseded worker cannot commit.
            state = 'FAILED' if error else 'REVIEW'
            conn.execute(update(jobs).where(jobs.c.id == job_id).values(state=state,
                revision=row['revision']+1, artifact_sha=digest, error=error, lease_token=None, lease_until=None))
            conn.execute(update(reservations).where(reservations.c.job_id == job_id).values(settled_units=0 if error else result.units))
            event(conn, job_id, 'failed' if error else 'preview_ready', {'reason':error} if error else result.model_dump())
            return True
