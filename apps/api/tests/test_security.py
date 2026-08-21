from datetime import timedelta

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import (
    create_session_token,
    decode_session_token,
    password_hasher,
)
from app.main import app
from app.services.rate_limit import SlidingWindowLimiter


def test_session_round_trip() -> None:
    token, csrf = create_session_token("admin")
    session = decode_session_token(token)
    assert session.username == "admin"
    assert session.csrf_token == csrf


def test_invalid_session_rejected() -> None:
    try:
        decode_session_token("invalid")
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("invalid session should be rejected")


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowLimiter(limit=2, window=timedelta(minutes=1))
    assert limiter.allow("client")
    assert limiter.allow("client")
    assert not limiter.allow("client")


def test_admin_session_requires_origin_and_csrf(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password_hash", password_hasher.hash("test-password"))
    monkeypatch.setattr(
        "app.api.routes.auth.login_limiter",
        SlidingWindowLimiter(limit=10, window=timedelta(minutes=15)),
    )
    client = TestClient(app)

    rejected = client.post(
        "/api/v1/admin/session",
        json={"username": settings.admin_username, "password": "test-password"},
    )
    assert rejected.status_code == 403

    login = client.post(
        "/api/v1/admin/session",
        headers={"Origin": settings.web_origin},
        json={"username": settings.admin_username, "password": "test-password"},
    )
    assert login.status_code == 200
    assert "HttpOnly" in login.headers["set-cookie"]
    csrf = login.json()["data"]["csrf_token"]

    rejected_logout = client.delete(
        "/api/v1/admin/session",
        headers={"X-CSRF-Token": csrf},
    )
    assert rejected_logout.status_code == 403

    logout = client.delete(
        "/api/v1/admin/session",
        headers={"Origin": settings.web_origin, "X-CSRF-Token": csrf},
    )
    assert logout.status_code == 200
