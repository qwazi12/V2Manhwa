"""Authenticated local Phase 0 API. No production identities or live providers."""
import time
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, delete, text
from .config import Settings
from .database import engine_for, sessions
from .repository import Repository
from .security import require_owner, login, COOKIE
from .storage import Storage
from .models import JobResponse, IdentityResponse, PreviewResponse
from .product_db import ProductDB
from .product_routes import router as product_router

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str = Field(min_length=1, max_length=256)

class JobRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=128)
    source_kind: str = Field(default='synthetic', pattern='^synthetic$')

    @field_validator('title')
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError('A title is required')
        return value.strip()

class CancelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=1)


def create_app(settings=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings or Settings.load()
        app.state.engine = engine_for(app.state.settings)
        app.state.repo = Repository(app.state.engine)
        app.state.product = ProductDB(app.state.engine)
        app.state.storage = Storage(app.state.settings)
        app.state.login_attempts = []
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title='Flamingo Next Studio — local foundation', version='0.1.0',
        docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    @app.middleware('http')
    async def private_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.get('/api/v1/healthz')
    def health():
        return {'status':'alive', 'service':'v2manhwa-local'}

    @app.get('/api/v1/readyz')
    def ready(request: Request, response: Response):
        try:
            with request.app.state.engine.connect() as conn:
                conn.execute(select(sessions.c.id).limit(1))
            request.app.state.storage.client.head_bucket(Bucket=request.app.state.settings.bucket)
        except Exception:
            response.status_code = 503
            return {'status':'unavailable', 'phase0_complete':False}
        return {'status':'ready-local', 'phase0_complete':False}

    @app.post('/api/v1/auth/login', response_model=IdentityResponse)
    def sign_in(body: LoginRequest, request: Request, response: Response):
        return login(request, response, body.key)

    @app.post('/api/v1/auth/logout', status_code=204)
    def sign_out(request: Request, response: Response, owner=Depends(require_owner)):
        with request.app.state.engine.begin() as conn:
            conn.execute(delete(sessions).where(sessions.c.id == owner['id']))
        response.delete_cookie(COOKIE, path='/api')

    @app.get('/api/v1/me', response_model=IdentityResponse)
    def me(owner=Depends(require_owner)):
        return {'role':'owner', 'csrf':owner['csrf'], 'mode':'local-studio'}

    @app.get('/api/v1/capabilities')
    def capabilities(owner=Depends(require_owner)):
        from .voice_models import installed
        return {'phase0_complete':False, 'publishing_enabled':False, 'drive_auto_copy_enabled':False,
                'autopilot_mode':'OFF', 'external_provider_calls_enabled':False,
                'provider':'local-system-speech-and-manual-editorial', 'daily_mock_budget_units':100,
                'local_features':{'source_ingestion':True,'ocr':'tesseract-english-unreviewed','narration':'offline-system-or-kokoro','neural_voice_files_present':installed(),'render':'ffmpeg-mp4','technical_qa':True,'semantic_qa':'human_required'},
                'live_integrations':{'ai_models':'unconfigured','youtube':'disconnected','analytics':'manual-import-only','cloud':'not-deployed'}}

    @app.get('/api/v1/jobs', response_model=list[JobResponse])
    def list_jobs(request: Request, owner=Depends(require_owner)):
        return request.app.state.repo.list()

    @app.post('/api/v1/jobs', status_code=201, response_model=JobResponse)
    def create_job(body: JobRequest, request: Request, idempotency_key: str = Header(min_length=8, max_length=160), owner=Depends(require_owner)):
        return request.app.state.repo.create(body.title, idempotency_key)

    @app.get('/api/v1/jobs/{job_id}', response_model=JobResponse)
    def get_job(job_id: UUID, request: Request, owner=Depends(require_owner)):
        return request.app.state.repo.get(str(job_id))

    @app.post('/api/v1/jobs/{job_id}/cancel', response_model=JobResponse)
    def cancel(job_id: UUID, body: CancelRequest, request: Request, owner=Depends(require_owner)):
        return request.app.state.repo.cancel(str(job_id), body.revision)

    @app.get('/api/v1/jobs/{job_id}/preview', response_model=PreviewResponse)
    def preview(job_id: UUID, request: Request, owner=Depends(require_owner)):
        job = request.app.state.repo.get(str(job_id))
        if job['state'] != 'REVIEW' or not job['artifact_sha']:
            raise HTTPException(409, 'A verified preview is not available')
        digest = job['artifact_sha']
        expires = int(time.time()) + 300
        signature = request.app.state.storage.signature(digest, owner['id'], expires)
        return {'url':f'/api/v1/media/{digest}?expires={expires}&signature={signature}', 'sha256':digest, 'expires_at':expires}

    @app.get('/api/v1/media/{digest}')
    def media(digest: str, expires: int, signature: str, request: Request, owner=Depends(require_owner)):
        request.app.state.storage.verify(digest, owner['id'], expires, signature)
        data = request.app.state.storage.get(digest)
        return Response(data, media_type='image/svg+xml', headers={
            'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; sandbox",
            'Content-Disposition':'inline; filename="synthetic-preview.svg"'})

    @app.get('/api/v1/openapi.json')
    def schema(owner=Depends(require_owner)):
        return app.openapi()

    from .body_limit import BodyLimitMiddleware
    app.add_middleware(BodyLimitMiddleware)
    app.include_router(product_router)
    return app

app = create_app()
