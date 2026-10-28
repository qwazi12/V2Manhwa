"""Create fresh keys in an ignored file, without reading existing app settings."""
from pathlib import Path
import secrets
import os
root = Path(__file__).resolve().parents[1]
path = root / '.env.local'
if not path.exists():
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(f'ENVIRONMENT=local\nFNS_LOCAL_DEV_KEY={secrets.token_urlsafe(36)}\nFNS_MEDIA_SIGNING_KEY={secrets.token_urlsafe(36)}\n')
    print('Created private local settings in .env.local')
else:
    print('Using existing .env.local')
