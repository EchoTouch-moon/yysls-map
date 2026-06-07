from datetime import timedelta

from fastapi import HTTPException

from app.core.security import create_session_token, decode_session_token
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

