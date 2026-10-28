"""Local-only settings: refuse remote infrastructure and all live providers."""
import os
from urllib.parse import urlparse
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    database_url: str
    storage_endpoint: str
    bucket: str
    storage_user: str
    storage_password: str
    owner_key: str
    signing_key: str
    web_origin: str

    @classmethod
    def load(cls):
        if os.getenv('ENVIRONMENT', 'local') != 'local':
            raise RuntimeError('This milestone supports local development only')
        db = os.getenv('FNS_DATABASE_URL', 'postgresql+psycopg://fns_local:local_dev_only_not_a_real_secret@127.0.0.1:56473/fns_local')
        storage = os.getenv('FNS_STORAGE_ENDPOINT', 'http://127.0.0.1:59473')
        origin = os.getenv('FNS_WEB_ORIGIN', 'http://127.0.0.1:3000')
        for url in (db, storage, origin):
            if urlparse(url).hostname not in {'127.0.0.1', 'localhost'}:
                raise RuntimeError('Only independent loopback services are allowed')
        if urlparse(db).scheme != 'postgresql+psycopg' or urlparse(db).path not in {'/fns_local', '/fns_test'}:
            raise RuntimeError('Use the dedicated fns_local or fns_test PostgreSQL database')
        for key in ('PUBLISHING_ENABLED', 'DRIVE_AUTO_COPY_ENABLED', 'ALLOW_PROTECTED_SOURCE_SCRAPING'):
            if os.getenv(key, 'false').lower() != 'false':
                raise RuntimeError(f'{key} must remain false')
        if os.getenv('AUTOPILOT_MODE', 'OFF') != 'OFF':
            raise RuntimeError('Autopilot must remain OFF')
        owner = os.getenv('FNS_LOCAL_DEV_KEY', '')
        signing = os.getenv('FNS_MEDIA_SIGNING_KEY', '')
        if len(owner) < 32 or len(signing) < 32:
            raise RuntimeError('Generate local owner and media keys with scripts/setup_local.py')
        return cls(db, storage, 'v2manhwa-synthetic', 'fns_local_only',
                   'local_dev_only_not_a_real_secret', owner, signing, origin)
