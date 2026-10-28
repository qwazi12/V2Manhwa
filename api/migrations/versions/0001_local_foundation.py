"""Frozen local synthetic schema. Full product schema is a separate future migration."""
from alembic import op
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('''CREATE TABLE local_sessions (
      id varchar(64) PRIMARY KEY, csrf varchar(80) NOT NULL, expires_at double precision NOT NULL)''')
    op.execute('''CREATE TABLE local_jobs (
      id varchar(36) PRIMARY KEY, title varchar(128) NOT NULL,
      state varchar(24) NOT NULL CHECK(state IN ('QUEUED','RUNNING','REVIEW','CANCELLED','FAILED')),
      revision integer NOT NULL, idempotency_key varchar(160) NOT NULL UNIQUE,
      input_hash varchar(64) NOT NULL, attempt integer NOT NULL,
      lease_token varchar(64), lease_until double precision,
      artifact_sha varchar(64), error varchar(256), created_at timestamptz NOT NULL)''')
    op.execute('''CREATE TABLE local_events (
      id varchar(36) PRIMARY KEY, job_id varchar(36) NOT NULL REFERENCES local_jobs(id),
      kind varchar(64) NOT NULL, detail json NOT NULL, created_at timestamptz NOT NULL)''')
    op.execute('''CREATE TABLE local_budget_reservations (
      job_id varchar(36) PRIMARY KEY REFERENCES local_jobs(id),
      reserved_units integer NOT NULL CHECK(reserved_units >= 0 AND reserved_units <= 5),
      settled_units integer CHECK(settled_units >= 0 AND settled_units <= reserved_units))''')

def downgrade():
    for name in ('local_budget_reservations','local_events','local_jobs','local_sessions'):
        op.drop_table(name)
