from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.contracts import AdminLogin, SessionData
from app.core.config import settings
from app.core.security import (
    SESSION_COOKIE,
    AdminSession,
    create_session_token,
    require_admin,
    validate_request_origin,
    verify_admin_password,
)
from app.schemas import ApiResponse
from app.services.rate_limit import login_limiter

router = APIRouter(prefix="/admin/session", tags=["admin"])


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("", response_model=ApiResponse[SessionData])
def create_admin_session(
    credentials: AdminLogin,
    request: Request,
    response: Response,
) -> ApiResponse[SessionData]:
    validate_request_origin(request)
    if not login_limiter.allow(_client_key(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试过于频繁，请稍后再试。",
        )
    if not verify_admin_password(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误。",
        )
    token, csrf_token = create_session_token(credentials.username)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        max_age=settings.session_ttl_minutes * 60,
        path="/api/v1/admin",
    )
    return ApiResponse(
        data=SessionData(
            username=credentials.username,
            csrf_token=csrf_token,
            expires_in_minutes=settings.session_ttl_minutes,
        )
    )


@router.delete("", response_model=ApiResponse[dict[str, bool]])
def delete_admin_session(
    response: Response,
    _: Annotated[AdminSession, Depends(require_admin)],
) -> ApiResponse[dict[str, bool]]:
    response.delete_cookie(SESSION_COOKIE, path="/api/v1/admin")
    return ApiResponse(data={"logged_out": True})

