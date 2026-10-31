"""Initialize only the dedicated Compose services; wait for private storage."""
import time
from alembic import command
from alembic.config import Config
from flamingo_next_api.config import Settings
from flamingo_next_api.storage import Storage
settings=Settings.load()
command.upgrade(Config('api/alembic.ini'),'head')
for attempt in range(30):
    try:
        Storage(settings).initialize()
        break
    except Exception:
        if attempt==29:raise
        time.sleep(1)
