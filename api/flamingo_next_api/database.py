"""Persistent Phase 0 records. Separate from the future full product schema."""
from datetime import datetime, timezone
from sqlalchemy import (MetaData, Table, Column, String, Integer, Float, DateTime,
                        JSON, ForeignKey, CheckConstraint, create_engine)

metadata = MetaData()
def now():
    return datetime.now(timezone.utc)

sessions = Table('local_sessions', metadata,
    Column('id', String(64), primary_key=True), Column('csrf', String(80), nullable=False),
    Column('expires_at', Float, nullable=False))
jobs = Table('local_jobs', metadata,
    Column('id', String(36), primary_key=True),
    Column('title', String(128), nullable=False),
    Column('state', String(24), nullable=False),
    Column('revision', Integer, nullable=False, default=1),
    Column('idempotency_key', String(160), nullable=False, unique=True),
    Column('input_hash', String(64), nullable=False),
    Column('attempt', Integer, nullable=False, default=0),
    Column('lease_token', String(64)), Column('lease_until', Float),
    Column('artifact_sha', String(64)), Column('error', String(256)),
    Column('created_at', DateTime(timezone=True), nullable=False, default=now),
    CheckConstraint("state IN ('QUEUED','RUNNING','REVIEW','CANCELLED','FAILED')"))
events = Table('local_events', metadata,
    Column('id', String(36), primary_key=True),
    Column('job_id', ForeignKey('local_jobs.id'), nullable=False),
    Column('kind', String(64), nullable=False),
    Column('detail', JSON, nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=False, default=now))
reservations = Table('local_budget_reservations', metadata,
    Column('job_id', ForeignKey('local_jobs.id'), primary_key=True),
    Column('reserved_units', Integer, nullable=False),
    Column('settled_units', Integer),
    CheckConstraint('reserved_units >= 0 AND reserved_units <= 5'),
    CheckConstraint('settled_units >= 0 AND settled_units <= reserved_units'))

def engine_for(settings):
    return create_engine(settings.database_url, pool_pre_ping=True)
