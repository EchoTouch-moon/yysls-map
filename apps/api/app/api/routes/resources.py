"""Public read endpoints for content resources.

List endpoints return only PUBLISHED items and apply the shared spoiler
policy.  Source is only accessible by id (never publicly listed).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import ProgressKey
from app.schemas import (
    ApiResponse,
    ChapterRead,
    CharacterListItem,
    CharacterRead,
    FactionRead,
    ResponseMeta,
    SourceRead,
    StoryEventRead,
)
from app.services import content as svc
from app.services.spoiler import context_for

router = APIRouter(prefix="/resources", tags=["resources"])


# ── chapter ───────────────────────────────────────────────────────────


@router.get("/chapters", response_model=ApiResponse[list[ChapterRead]])
def list_chapters(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[ChapterRead]]:
    rows, next_cursor = svc.list_chapters(
        db,
        context=context_for(progress),
        cursor=cursor,
        limit=limit,
    )
    return ApiResponse(
        data=[ChapterRead.model_validate(r) for r in rows],
        meta=ResponseMeta(next_cursor=next_cursor),
    )


@router.get("/chapters/{slug}", response_model=ApiResponse[ChapterRead])
def get_chapter(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[ChapterRead]:
    ch = svc.get_chapter_by_slug(db, slug, context=context_for(progress))
    if ch is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ApiResponse(data=ChapterRead.model_validate(ch))


# ── faction ───────────────────────────────────────────────────────────


@router.get("/factions", response_model=ApiResponse[list[FactionRead]])
def list_factions(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[FactionRead]]:
    ctx = context_for(progress)
    rows, next_cursor = svc.list_factions_published(
        db, context=ctx, cursor=cursor, limit=limit
    )
    return ApiResponse(
        data=[FactionRead.model_validate(r) for r in rows],
        meta=ResponseMeta(next_cursor=next_cursor),
    )


@router.get("/factions/{slug}", response_model=ApiResponse[FactionRead])
def get_faction(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[FactionRead]:
    ctx = context_for(progress)
    f = svc.get_faction_by_slug_published(db, slug, context=ctx)
    if f is None:
        raise HTTPException(status_code=404, detail="Faction not found")
    return ApiResponse(data=FactionRead.model_validate(f))


# ── character ─────────────────────────────────────────────────────────


@router.get("/characters", response_model=ApiResponse[list[CharacterListItem]])
def list_characters(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[CharacterListItem]]:
    ctx = context_for(progress)
    rows, next_cursor = svc.list_characters_published(
        db, context=ctx, cursor=cursor, limit=limit
    )
    return ApiResponse(
        data=[CharacterListItem.model_validate(r) for r in rows],
        meta=ResponseMeta(next_cursor=next_cursor),
    )


@router.get("/characters/{slug}", response_model=ApiResponse[CharacterRead])
def get_character(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[CharacterRead]:
    ctx = context_for(progress)
    c = svc.get_character_by_slug_published(db, slug, context=ctx)
    if c is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return ApiResponse(data=CharacterRead.model_validate(c))


# ── story event ───────────────────────────────────────────────────────


@router.get("/events", response_model=ApiResponse[list[StoryEventRead]])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[StoryEventRead]]:
    ctx = context_for(progress)
    rows, next_cursor = svc.list_events_published(
        db, context=ctx, cursor=cursor, limit=limit
    )
    return ApiResponse(
        data=[StoryEventRead.model_validate(r) for r in rows],
        meta=ResponseMeta(next_cursor=next_cursor),
    )


@router.get("/events/{slug}", response_model=ApiResponse[StoryEventRead])
def get_event(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[StoryEventRead]:
    ctx = context_for(progress)
    e = svc.get_event_by_slug_published(db, slug, context=ctx)
    if e is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return ApiResponse(data=StoryEventRead.model_validate(e))


# ── source (by id only, never listed) ─────────────────────────────────


@router.get("/sources/{source_id}", response_model=ApiResponse[SourceRead])
def get_source(
    source_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[SourceRead]:
    s = svc.get_source_by_id_published(
        db, source_id, context=context_for(progress)
    )
    if s is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return ApiResponse(data=SourceRead.model_validate(s))
