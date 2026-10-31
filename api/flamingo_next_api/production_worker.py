"""Separate offline render worker with cancellable subprocesses and lease renewal."""
import logging
import signal
import threading
from sqlalchemy import select
from .config import Settings
from .database import engine_for
from .product_db import ProductDB
from .render_jobs import RenderJobs
from .editorial import require_internal_rights
from .storage import Storage
from .media_engine import MediaEngine,Cancelled
log=logging.getLogger(__name__)

def run_once(db,storage,stopping=None):
    jobs=RenderJobs(db);job=jobs.claim()
    if not job:return False
    def heartbeat():
        return not (stopping and stopping.is_set()) and jobs.heartbeat(job['id'],job['lease_token'])
    try:
        with db.engine.connect() as conn:
            record=db.load(conn,job['production_id']);require_internal_rights(record)
            table=db.tables['media_assets']
            ids=[p['asset_id'] for p in record['pages']]
            assets={str(r['id']):dict(r) for r in conn.execute(select(table).where(table.c.id.in_(ids))).mappings()}
        if job['kind']=='analysis':
            from .source_analysis import SourceAnalyzer
            result=SourceAnalyzer(storage,heartbeat).analyze(record,assets)
        else:
            result=MediaEngine(storage,heartbeat).render(record,assets,job['kind'])
        jobs.finish(job,result)
    except Cancelled:
        # Cancellation is persisted by API. A shutdown leaves an expiring lease.
        log.info('Render stopped: %s',job['id'])
    except Exception as e:
        log.exception('Local render failed for %s',job['id'])
        jobs.finish(job,error=str(e)[:1500])
    return True

def main():
    settings=Settings.load();engine=engine_for(settings);db=ProductDB(engine);storage=Storage(settings)
    stop=threading.Event()
    signal.signal(signal.SIGINT,lambda *_:stop.set());signal.signal(signal.SIGTERM,lambda *_:stop.set())
    try:
        while not stop.is_set():
            if not run_once(db,storage,stop):stop.wait(1)
    finally:engine.dispose()

if __name__=='__main__':main()
