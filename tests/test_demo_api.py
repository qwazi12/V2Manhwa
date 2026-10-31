"""Real PostgreSQL + S3 fixture integration. Never uses product/provider accounts."""
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text, select, update
from flamingo_next_api.config import Settings
from flamingo_next_api.database import engine_for, metadata, jobs, reservations, events
from flamingo_next_api.main import create_app
from flamingo_next_api.gateway import FakeGateway, FakeResult
from flamingo_next_api.storage import Storage
from flamingo_next_api.repository import Repository
from flamingo_next_api.worker import run_once

KEY = 'test-only-original-local-owner-key-123456789'
SIGN = 'test-only-original-media-signing-key-987654321'
ORIGIN = 'http://127.0.0.1:3000'

@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'local')
    monkeypatch.setenv('FNS_LOCAL_DEV_KEY', KEY)
    monkeypatch.setenv('FNS_MEDIA_SIGNING_KEY', SIGN)
    monkeypatch.setenv('FNS_DATABASE_URL', 'postgresql+psycopg://fns_local:local_dev_only_not_a_real_secret@127.0.0.1:56473/fns_test')
    return replace(Settings.load(), bucket='v2manhwa-synthetic-test')

@pytest.fixture
def services(settings):
    engine = engine_for(settings)
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text('TRUNCATE local_events, local_budget_reservations, local_jobs, local_sessions CASCADE'))
    storage = Storage(settings)
    storage.initialize()
    yield Repository(engine), storage
    engine.dispose()

@pytest.fixture
def client(settings, services):
    with TestClient(create_app(settings)) as c:
        yield c

def auth(c):
    response = c.post('/api/v1/auth/login', json={'key':KEY}, headers={'Origin':ORIGIN})
    assert response.status_code == 200, response.text
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'samesite=strict' in response.headers['set-cookie'].lower()
    return {'Origin':ORIGIN, 'X-CSRF-Token':response.json()['csrf'], 'Idempotency-Key':str(uuid4())}

def create(c, headers, title='Original synthetic fixture'):
    return c.post('/api/v1/jobs', json={'title':title}, headers=headers)

def test_health_auth_and_csrf(client):
    assert client.get('/api/v1/healthz').status_code == 200
    assert client.get('/api/v1/readyz').json()['phase0_complete'] is False
    for path in ('/api/v1/me','/api/v1/jobs','/api/v1/capabilities','/api/v1/openapi.json'):
        assert client.get(path).status_code == 401
    assert client.get('/docs').status_code == 404
    assert client.post('/api/v1/auth/login', json={'key':KEY}).status_code == 403
    h = auth(client)
    assert create(client, {'Origin':ORIGIN, 'Idempotency-Key':str(uuid4())}).status_code == 403
    assert create(client, h | {'Origin':'https://evil.invalid'}).status_code == 403
    caps = client.get('/api/v1/capabilities').json()
    assert not caps['publishing_enabled'] and not caps['external_provider_calls_enabled']
    assert client.post('/api/v1/auth/logout', headers=h).status_code == 204
    assert client.get('/api/v1/jobs').status_code == 401

def test_idempotency_validation_and_restart(client, settings):
    h = auth(client)
    first = create(client, h)
    assert first.status_code == 201
    assert first.json()['state'] == 'QUEUED'
    assert create(client, h).json()['id'] == first.json()['id']
    assert create(client, h, 'Changed title').status_code == 409
    assert create(client, h, '   ').status_code == 422
    assert client.post('/api/v1/jobs',json={'title':'No', 'source_kind':'webtoon'},headers=h).status_code == 422
    # New API instance/connection pool, same persistent session and job.
    with TestClient(create_app(settings)) as fresh:
        fresh.cookies.update(client.cookies)
        assert fresh.get('/api/v1/jobs').json()[0]['id'] == first.json()['id']

def test_private_preview_tamper_expiry_and_wrong_session(client, settings, services):
    h = auth(client)
    job = create(client,h).json()
    repo, storage = services
    assert run_once(repo, storage)
    done = client.get(f"/api/v1/jobs/{job['id']}").json()
    assert done['state'] == 'REVIEW'
    assert done['budget']['settled_units'] == 2
    preview = client.get(f"/api/v1/jobs/{job['id']}/preview").json()
    assert client.get(preview['url']).status_code == 200
    assert 'no-store' in client.get(preview['url']).headers['cache-control']
    with TestClient(create_app(settings)) as other:
        assert other.get(preview['url']).status_code == 401
        auth(other)
        assert other.get(preview['url']).status_code == 403
    assert client.get(preview['url'].replace(done['artifact_sha'], 'a'*64)).status_code == 403
    signature = storage.signature(done['artifact_sha'], 'wrong-user', int(time.time())-1)
    assert client.get(f"/api/v1/media/{done['artifact_sha']}?expires={int(time.time())-1}&signature={signature}").status_code == 403
    assert storage.client.get_bucket_policy_status(Bucket=settings.bucket)['PolicyStatus']['IsPublic'] is False
    storage.client.put_object(Bucket=settings.bucket, Key=f"synthetic/{done['artifact_sha']}.svg", Body=b'corrupt')
    assert client.get(preview['url']).status_code == 409

def test_cancel_stale_revision_and_fenced_worker(client, services):
    h = auth(client)
    job = create(client,h).json()
    repo, storage = services
    claimed = repo.claim()
    path = f"/api/v1/jobs/{job['id']}/cancel"
    assert client.post(path,json={'revision':1},headers=h).status_code == 409
    assert client.post(path,json={'revision':claimed['revision']},headers=h).json()['state'] == 'CANCELLED'
    assert not repo.finish(job['id'], claimed['lease_token'], 'a'*64, FakeGateway().execute(claimed['budget']))
    assert repo.claim() is None
    assert Repository(repo.engine).get(job['id'])['state'] == 'CANCELLED'

def test_concurrent_idempotency_and_claims(services):
    repo, storage = services
    with ThreadPoolExecutor(6) as pool:
        results = list(pool.map(lambda _:repo.create('Concurrent fixture','same-idempotency-key'),range(6)))
    assert len({r['id'] for r in results}) == 1
    with ThreadPoolExecutor(6) as pool:
        claims = list(pool.map(lambda _:repo.claim(),range(6)))
    assert sum(c is not None for c in claims) == 1
    claim = next(c for c in claims if c)
    # Recover an expired lease; reject a late result from the old owner.
    with repo.engine.begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == claim['id']).values(lease_until=time.time()-1))
    recovered = repo.claim()
    assert recovered['attempt'] == 2
    result = FakeGateway().execute(recovered['budget'])
    assert not repo.finish(claim['id'],claim['lease_token'],'a'*64,result)
    assert repo.finish(recovered['id'],recovered['lease_token'],storage.put(b'<svg/>'),result)
    assert [e['kind'] for e in repo.get(claim['id'])['events']] == ['queued','worker_claimed','worker_claimed','preview_ready']

def test_budget_gate_and_untrusted_results(services):
    repo, _ = services
    for i in range(50):
        repo.create(f'Budget fixture {i}',f'budget-idempotency-{i}')
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        repo.create('Over budget','budget-over-limit')
    assert error.value.status_code == 409
    with pytest.raises(ValueError):
        FakeGateway().execute(None)
    with pytest.raises(ValueError):
        FakeGateway().execute({'reserved_units':1,'settled_units':None})
    with pytest.raises(ValueError):
        FakeResult.model_validate({'provider':'real-provider','units':3,'summary':'Untrusted'})

def test_environment_fails_closed(settings, monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','production')
    with pytest.raises(RuntimeError): Settings.load()
    monkeypatch.setenv('ENVIRONMENT','local')
    monkeypatch.setenv('FNS_DATABASE_URL','postgresql+psycopg://example.invalid/fns_local')
    with pytest.raises(RuntimeError): Settings.load()
