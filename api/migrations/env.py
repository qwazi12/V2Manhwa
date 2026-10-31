from alembic import context
from flamingo_next_api.config import Settings
from flamingo_next_api.database import metadata, engine_for
with engine_for(Settings.load()).connect() as connection:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()
