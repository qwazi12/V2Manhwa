"""Revocable local sessions. Production OIDC and invited roles remain deferred."""
import hashlib
import hmac
import secrets
import time
from fastapi import HTTPException, Request
from sqlalchemy import select, delete
from .database import sessions

COOKIE = 'fns_local_session'
TTL = 8 * 60 * 60

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def check_origin(request: Request):
    if request.headers.get('origin') != request.app.state.settings.web_origin:
        raise HTTPException(403, 'Origin does not match the local studio')

def require_owner(request: Request):
    token = request.cookies.get(COOKIE, '')
    with request.app.state.engine.begin() as conn:
        row = conn.execute(select(sessions).where(sessions.c.id == token_hash(token))).mappings().first()
    if not row or row['expires_at'] <= time.time():
        raise HTTPException(401, 'Sign in to the local studio')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        check_origin(request)
        if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), row['csrf']):
            raise HTTPException(403, 'CSRF token missing or invalid')
    return dict(row)

def login(request, response, key):
    check_origin(request)
    # Bounded attempts for the single local API process; no plaintext key is persisted.
    with request.app.state.engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text('SELECT pg_advisory_xact_lock(246818)'))
        conn.execute(delete(sessions).where(sessions.c.expires_at <= time.time()))
        attempts = request.app.state.login_attempts
        current = time.monotonic()
        attempts[:] = [t for t in attempts if current - t < 60]
        if len(attempts) >= 10:
            raise HTTPException(429, 'Too many attempts; wait one minute')
        if not hmac.compare_digest(key, request.app.state.settings.owner_key):
            attempts.append(current)
            raise HTTPException(401, 'Incorrect local access key')
        old = request.cookies.get(COOKIE)
        if old:
            conn.execute(delete(sessions).where(sessions.c.id == token_hash(old)))
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        conn.execute(sessions.insert().values(id=token_hash(token), csrf=csrf, expires_at=time.time() + TTL))
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite='strict', secure=False, path='/api')
    return {'role': 'owner', 'csrf': csrf, 'mode': 'local-synthetic'}
