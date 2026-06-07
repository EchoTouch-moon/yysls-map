import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import (
    PublicSubmissionCreate,
    ReviewSubmission,
    SubmissionAdminRead,
    SubmissionPublicReceipt,
)
from app.core.security import AdminSession, require_admin
from app.db import get_db
from app.domain import SubmissionStatus
from app.models import Submission
from app.schemas import ApiResponse
from app.services.rate_limit import submission_limiter
from app.services.submissions import create_submission, review_submission

router = APIRouter(tags=["submissions"])


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/submissions", response_model=ApiResponse[SubmissionPublicReceipt], status_code=201)
def submit_content(
    body: PublicSubmissionCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[SubmissionPublicReceipt]:
    if body.website:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="投稿格式无效。")
    if not submission_limiter.allow(_client_key(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="投稿过于频繁，请稍后再试。",
        )
    submission = create_submission(
        db,
        submission_type=body.submission_type,
        payload=body.payload,
        source_note=body.source_note,
        contact=body.contact,
    )
    return ApiResponse(
        data=SubmissionPublicReceipt(
            id=submission.id,
            status=submission.status,
            message="投稿已进入人工审核，不会自动公开。",
        )
    )


@router.get("/admin/submissions", response_model=ApiResponse[list[SubmissionAdminRead]])
def list_submissions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[AdminSession, Depends(require_admin)],
    submission_status: Annotated[
        SubmissionStatus, Query(alias="status")
    ] = SubmissionStatus.PENDING,
) -> ApiResponse[list[SubmissionAdminRead]]:
    submissions = db.scalars(
        select(Submission)
        .where(Submission.status == submission_status)
        .order_by(Submission.created_at.asc(), Submission.id.asc())
        .limit(100)
    ).all()
    return ApiResponse(data=[SubmissionAdminRead.model_validate(item) for item in submissions])


@router.patch(
    "/admin/submissions/{submission_id}",
    response_model=ApiResponse[SubmissionAdminRead],
)
def review_submission_route(
    submission_id: uuid.UUID,
    body: ReviewSubmission,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminSession, Depends(require_admin)],
) -> ApiResponse[SubmissionAdminRead]:
    submission = review_submission(
        db,
        submission_id=submission_id,
        action=body.action,
        review_note=body.review_note,
        reviewer=admin.username,
    )
    return ApiResponse(data=SubmissionAdminRead.model_validate(submission))
