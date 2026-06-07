import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.contracts import (
    AdminChapterRead,
    AdminChapterWrite,
    AdminCharacterRead,
    AdminCharacterWrite,
    AdminContentBootstrap,
    AdminEventRead,
    AdminEventWrite,
    AdminFactionRead,
    AdminFactionWrite,
    AdminRelationshipRead,
    AdminRelationshipWrite,
    ArchiveResult,
)
from app.core.security import AdminSession, require_admin
from app.db import get_db
from app.schemas import ApiResponse
from app.services import admin_content

router = APIRouter(prefix="/admin/content", tags=["admin-content"])
AdminDependency = Annotated[AdminSession, Depends(require_admin)]
DatabaseDependency = Annotated[Session, Depends(get_db)]


@router.get("/bootstrap", response_model=ApiResponse[AdminContentBootstrap])
def get_bootstrap(
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminContentBootstrap]:
    return ApiResponse(data=admin_content.get_bootstrap(db))


@router.post(
    "/chapters",
    response_model=ApiResponse[AdminChapterRead],
    status_code=status.HTTP_201_CREATED,
)
def create_chapter(
    body: AdminChapterWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminChapterRead]:
    return ApiResponse(data=admin_content.create_chapter(db, body))


@router.patch(
    "/chapters/{row_id}",
    response_model=ApiResponse[AdminChapterRead],
)
def update_chapter(
    row_id: uuid.UUID,
    body: AdminChapterWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminChapterRead]:
    return ApiResponse(data=admin_content.update_chapter(db, row_id, body))


@router.post(
    "/factions",
    response_model=ApiResponse[AdminFactionRead],
    status_code=status.HTTP_201_CREATED,
)
def create_faction(
    body: AdminFactionWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminFactionRead]:
    return ApiResponse(data=admin_content.create_faction(db, body))


@router.patch(
    "/factions/{row_id}",
    response_model=ApiResponse[AdminFactionRead],
)
def update_faction(
    row_id: uuid.UUID,
    body: AdminFactionWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminFactionRead]:
    return ApiResponse(data=admin_content.update_faction(db, row_id, body))


@router.post(
    "/characters",
    response_model=ApiResponse[AdminCharacterRead],
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    body: AdminCharacterWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminCharacterRead]:
    return ApiResponse(data=admin_content.create_character(db, body))


@router.patch(
    "/characters/{row_id}",
    response_model=ApiResponse[AdminCharacterRead],
)
def update_character(
    row_id: uuid.UUID,
    body: AdminCharacterWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminCharacterRead]:
    return ApiResponse(data=admin_content.update_character(db, row_id, body))


@router.post(
    "/events",
    response_model=ApiResponse[AdminEventRead],
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    body: AdminEventWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminEventRead]:
    return ApiResponse(data=admin_content.create_event(db, body))


@router.patch(
    "/events/{row_id}",
    response_model=ApiResponse[AdminEventRead],
)
def update_event(
    row_id: uuid.UUID,
    body: AdminEventWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminEventRead]:
    return ApiResponse(data=admin_content.update_event(db, row_id, body))


@router.post(
    "/relationships",
    response_model=ApiResponse[AdminRelationshipRead],
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    body: AdminRelationshipWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminRelationshipRead]:
    return ApiResponse(data=admin_content.create_relationship(db, body))


@router.patch(
    "/relationships/{row_id}",
    response_model=ApiResponse[AdminRelationshipRead],
)
def update_relationship(
    row_id: uuid.UUID,
    body: AdminRelationshipWrite,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[AdminRelationshipRead]:
    return ApiResponse(data=admin_content.update_relationship(db, row_id, body))


@router.delete(
    "/{resource}/{row_id}",
    response_model=ApiResponse[ArchiveResult],
)
def archive_content(
    resource: str,
    row_id: uuid.UUID,
    db: DatabaseDependency,
    _: AdminDependency,
) -> ApiResponse[ArchiveResult]:
    return ApiResponse(data=admin_content.archive_content(db, resource, row_id))
