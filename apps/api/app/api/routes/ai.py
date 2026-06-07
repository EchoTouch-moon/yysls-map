from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.contracts import AIExtractionRequest, AIExtractionResult
from app.core.security import AdminSession, require_admin
from app.db import get_db
from app.schemas import ApiResponse
from app.services.llm import extract_and_audit

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])


@router.post("/extract", response_model=ApiResponse[AIExtractionResult])
async def extract_story_note(
    body: AIExtractionRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AdminSession, Depends(require_admin)],
) -> ApiResponse[AIExtractionResult]:
    return ApiResponse(data=await extract_and_audit(db, body.note))

