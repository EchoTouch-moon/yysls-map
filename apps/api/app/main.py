import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="燕云十六声剧情关系图谱 API",
    version="0.1.0",
    strict_content_type=True,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error("Unhandled request error", exc_info=exc, extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {"code": "internal_error", "message": "服务器暂时无法处理该请求。"},
            "meta": {"request_id": request_id},
        },
    )
