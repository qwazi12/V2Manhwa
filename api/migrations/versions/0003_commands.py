"""Idempotent mutation receipts for the product workflow."""
from alembic import op
revision='0003'
down_revision='0002'
branch_labels=None
depends_on=None

def upgrade():
    op.execute('''CREATE TABLE studio_commands (idempotency_key varchar(160) PRIMARY KEY,
      action text NOT NULL, input_sha char(64) NOT NULL, result jsonb NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now())''')

def downgrade(): op.drop_table('studio_commands')
