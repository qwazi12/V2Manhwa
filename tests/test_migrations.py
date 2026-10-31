from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from flamingo_next_api.database import metadata, engine_for
from test_demo_api import settings

def test_fresh_upgrade_downgrade_upgrade(settings):
    engine = engine_for(settings)
    # This fixture points only at the disposable fns_test database.
    assert engine.url.database == 'fns_test'
    config = Config(str(Path(__file__).resolve().parents[1] / 'api/alembic.ini'))
    if "alembic_version" in inspect(engine).get_table_names():
        command.downgrade(config,"base")
    metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    config = Config(str(Path(__file__).resolve().parents[1] / 'api/alembic.ini'))
    command.upgrade(config, 'head')
    assert set(metadata.tables).issubset(inspect(engine).get_table_names())
    command.downgrade(config, 'base')
    assert not set(metadata.tables).intersection(inspect(engine).get_table_names())
    command.upgrade(config, 'head')
    assert set(metadata.tables).issubset(inspect(engine).get_table_names())
    engine.dispose()
