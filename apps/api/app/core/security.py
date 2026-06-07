import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Cookie, Header, HTTPException, Request, status

from app.core.config import settings

SESSION_COOKIE = "yysls_admin_session"
CSRF_HEADER = "X-CSRF-Token"
ALGORITHM = "HS256"
password_hasher = PasswordHasher()


@dataclass(frozen=True)
class AdminSession:
    username: str
    csrf_token: str


def verify_admin_password(username: str, password: str) -> bool:
    if not hmac.compare_digest(username, settings.admin_username):
        return False
    if not settings.admin_password_hash:
        return False
    try:
        return password_hasher.verify(settings.admin_password_hash, password)
    except (InvalidHashError, VerifyMismatchError):
        return False


def create_session_token(username: str) -> tuple[str, str]:
    now = datetime.now(UTC)
    csrf_token = secrets.token_urlsafe(32)
    token = jwt.encode(
        {
            "sub": username,
            "csrf": csrf_token,
            "iat": now,
            "exp": now + timedelta(minutes=settings.session_ttl_minutes),
        },
        settings.session_secret,
        algorithm=ALGORITHM,
    )
    return token, csrf_token


def decode_session_token(token: str) -> AdminSession:
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
        username = payload["sub"]
        csrf_token = payload["csrf"]
        if not isinstance(username, str) or not isinstance(csrf_token, str):
            raise jwt.InvalidTokenError
        return AdminSession(username=username, csrf_token=csrf_token)
    except (jwt.InvalidTokenError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员会话无效或已过期。",
        ) from exc


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("Origin")
    allowed_origin = settings.web_origin.rstrip("/")
    if origin is None or not hmac.compare_digest(origin.rstrip("/"), allowed_origin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请求来源校验失败。",
        )


def require_admin(
    request: Request,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    csrf_token: Annotated[str | None, Header(alias=CSRF_HEADER)] = None,
) -> AdminSession:
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要管理员登录。")
    session = decode_session_token(session_token)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_request_origin(request)
        if csrf_token is None or not hmac.compare_digest(csrf_token, session.csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF 校验失败。",
            )
    return session
