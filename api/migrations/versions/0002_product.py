"""Frozen independent product schema and versioned workflow aggregate."""
from pathlib import Path
from alembic import op
import re
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None
SQL = Path(__file__).resolve().parents[1] / 'sql/0002_product.sql'

def upgrade():
    ddl = SQL.read_text().replace('BEGIN;', '').replace('COMMIT;', '')
    op.get_bind().exec_driver_sql(ddl)
    op.execute('''CREATE TABLE studio_episodes (
      production_id uuid PRIMARY KEY REFERENCES productions(id),
      revision integer NOT NULL CHECK(revision > 0),
      payload jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT now())''')
    op.execute('''CREATE TABLE studio_snapshots (
      production_id uuid NOT NULL REFERENCES productions(id), revision integer NOT NULL,
      payload jsonb NOT NULL, sha256 char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(production_id,revision))''')
    op.execute('''CREATE TABLE studio_render_jobs (
      id uuid PRIMARY KEY, production_id uuid NOT NULL REFERENCES productions(id),
      input_revision integer NOT NULL, input_sha char(64) NOT NULL, kind text NOT NULL DEFAULT 'longform',
      state text NOT NULL CHECK(state IN ('queued','running','completed','cancelled','failed')),
      idempotency_key text NOT NULL UNIQUE, lease_token text, lease_until double precision,
      attempt integer NOT NULL DEFAULT 0, cancel_requested boolean NOT NULL DEFAULT false,
      result jsonb, error text, created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(production_id,input_sha,kind))''')
    op.execute('''CREATE INDEX studio_render_claim ON studio_render_jobs(state,created_at)''')

def downgrade():
    for name in ('studio_render_jobs','studio_snapshots','studio_episodes'):
        op.drop_table(name)
    for name in reversed(re.findall(r'CREATE TABLE (\w+)',SQL.read_text())):
        op.execute(f'DROP TABLE IF EXISTS {name} CASCADE')
