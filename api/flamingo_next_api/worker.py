"""Independent local worker: fake gateway -> private synthetic cover -> review."""
import logging
import signal
import threading
from .config import Settings
from .database import engine_for
from .repository import Repository
from .storage import Storage
from .gateway import FakeGateway, PREVIEW

log = logging.getLogger(__name__)

def run_once(repo, storage):
    job = repo.claim()
    if not job:
        return False
    try:
        result = FakeGateway().execute(job['budget'])
        digest = storage.put(PREVIEW)
        storage.get(digest)  # Verify the frozen bytes before marking review-ready.
        repo.finish(job['id'], job['lease_token'], digest, result)
    except Exception:
        log.exception('Synthetic worker failed for job %s', job['id'])
        repo.finish(job['id'], job['lease_token'], error='Synthetic preview failed; inspect local worker log')
    return True

def main():
    settings = Settings.load()
    engine = engine_for(settings)
    storage = Storage(settings)
    storage.initialize()
    repo = Repository(engine)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        while not stop.is_set():
            if not run_once(repo, storage):
                stop.wait(1)
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
