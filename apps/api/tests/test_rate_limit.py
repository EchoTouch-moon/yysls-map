import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.security import password_hasher
from app.db import SessionLocal
from app.main import app
from app.models import RateLimitHit
from app.services.rate_limit import DatabaseSlidingWindowLimiter, SlidingWindowLimiter


def test_memory_limiter_allows_again_after_window() -> None:
    limiter = SlidingWindowLimiter(limit=1, window=timedelta(minutes=1))
    start = datetime(2026, 8, 21, 12, 0, 0, tzinfo=UTC)
    assert limiter.allow("client", now=start)
    assert not limiter.allow("client", now=start + timedelta(seconds=30))
    assert limiter.allow("client", now=start + timedelta(minutes=1, seconds=1))


def test_memory_limiter_tracks_keys_independently() -> None:
    limiter = SlidingWindowLimiter(limit=1, window=timedelta(minutes=1))
    start = datetime(2026, 8, 21, 12, 0, 0, tzinfo=UTC)
    assert limiter.allow("client-a", now=start)
    assert limiter.allow("client-b", now=start)
    assert not limiter.allow("client-a", now=start)


def _delete_bucket_rows(bucket: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(RateLimitHit).where(RateLimitHit.bucket_key == bucket))
        db.commit()


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)
def test_database_limiter_blocks_after_limit() -> None:
    limiter = DatabaseSlidingWindowLimiter(limit=2, window=timedelta(minutes=1))
    key = f"test-{uuid.uuid4().hex}"
    try:
        assert limiter.allow(key)
        assert limiter.allow(key)
        assert not limiter.allow(key)
        assert limiter.allow(f"other-{uuid.uuid4().hex}")
    finally:
        _delete_bucket_rows(key)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)
def test_database_limiter_expires_old_hits() -> None:
    limiter = DatabaseSlidingWindowLimiter(limit=1, window=timedelta(minutes=1))
    key = f"test-{uuid.uuid4().hex}"
    start = datetime.now(UTC)
    try:
        assert limiter.allow(key, now=start)
        assert not limiter.allow(key, now=start + timedelta(seconds=30))
        assert limiter.allow(key, now=start + timedelta(minutes=1, seconds=1))
    finally:
        _delete_bucket_rows(key)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)
def test_login_returns_429_when_database_limiter_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password_hash", password_hasher.hash("test-password"))
    from app.api.routes import auth

    monkeypatch.setattr(
        auth, "login_limiter", DatabaseSlidingWindowLimiter(limit=1, window=timedelta(minutes=1))
    )
    client = TestClient(app)
    payload = {"username": settings.admin_username, "password": "test-password"}
    headers = {"Origin": settings.web_origin}
    try:
        _delete_bucket_rows("testclient")
        first = client.post("/api/v1/admin/session", headers=headers, json=payload)
        assert first.status_code == 200
        second = client.post("/api/v1/admin/session", headers=headers, json=payload)
        assert second.status_code == 429
    finally:
        _delete_bucket_rows("testclient")
