import secrets
from datetime import datetime, timezone

from flask import current_app, request, session


CSRF_SESSION_KEY = '_csrf_token'


def utcnow():
    return datetime.now(timezone.utc)


def csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf():
    if current_app.config.get('TESTING') or not current_app.config.get('CSRF_ENABLED', True):
        return True
    if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
        return True

    expected = session.get(CSRF_SESSION_KEY)
    supplied = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    return bool(expected and supplied and secrets.compare_digest(expected, supplied))


def security_headers(response):
    headers = current_app.config.get('SECURITY_HEADERS', {})
    for name, value in headers.items():
        response.headers.setdefault(name, value)
    return response
