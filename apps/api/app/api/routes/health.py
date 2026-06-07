from fastapi import APIRouter

from app.core.config import settings
from app.schemas import ApiResponse, HealthData

router = APIRouter(tags=["system"])


@router.get("/health", response_model=ApiResponse[HealthData])
def health() -> ApiResponse[HealthData]:
    return ApiResponse(data=HealthData(status="ok", environment=settings.app_env))
