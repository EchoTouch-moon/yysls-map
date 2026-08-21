"""Reusable CRUD service for content resources.

All write helpers flush but never commit - the caller controls the transaction.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.domain import ContentStatus
from app.models import (
    Chapter,
    Character,
    Faction,
    Relationship,
    Source,
    StoryEvent,
)
from app.services.spoiler import SpoilerContext, is_visible

# ── types ─────────────────────────────────────────────────────────────

MAX_PAGE_SIZE = 100


class CursorModel(Protocol):
    id: UUID
    created_at: datetime


ModelT = TypeVar("ModelT", bound=CursorModel)


# ── cursor helpers ────────────────────────────────────────────────────


def encode_cursor(created_at: datetime, row_id: UUID) -> str:
    """Encode a deterministic (created_at, id) cursor as URL-safe base64."""
    payload = json.dumps(
        {"t": created_at.isoformat(), "i": str(row_id)},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Decode a cursor back to (created_at, id)."""
    payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    dt = datetime.fromisoformat(payload["t"])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt, UUID(payload["i"])


def _visible_page(
    db: Session,
    *,
    stmt: Select[tuple[ModelT]],
    cursor: str | None,
    limit: int,
    predicate: Callable[[ModelT], bool],
) -> tuple[list[ModelT], str | None]:
    page_size = max(1, min(limit, MAX_PAGE_SIZE))
    scan_cursor = decode_cursor(cursor) if cursor else None
    visible: list[ModelT] = []

    while len(visible) < page_size + 1:
        batch_stmt = stmt
        if scan_cursor:
            created_at, row_id = scan_cursor
            model = stmt.column_descriptions[0]["entity"]
            batch_stmt = batch_stmt.where(
                (model.created_at > created_at)
                | ((model.created_at == created_at) & (model.id > row_id))
            )
        batch = list(db.scalars(batch_stmt.limit(MAX_PAGE_SIZE)).all())
        if not batch:
            break
        visible.extend(item for item in batch if predicate(item))
        last = batch[-1]
        scan_cursor = (last.created_at, last.id)
        if len(batch) < MAX_PAGE_SIZE:
            break

    next_cursor = (
        encode_cursor(visible[page_size - 1].created_at, visible[page_size - 1].id)
        if len(visible) > page_size
        else None
    )
    return visible[:page_size], next_cursor


# ── spoiler helpers ──────────────────────────────────────────────────


def _chapter_rank_map(db: Session) -> dict[UUID, int]:
    return {
        cid: rank
        for cid, rank in db.execute(
            select(Chapter.id, Chapter.progress_rank)
        ).all()
    }


def _required_rank(
    ranks: dict[UUID, int],
    visible_after_chapter_id: UUID | None,
    first_appear_chapter_id: UUID | None = None,
) -> int | None:
    target = visible_after_chapter_id or first_appear_chapter_id
    if target is None:
        return None
    return ranks.get(target)


def passes_spoiler(
    *,
    spoiler_level: int,
    visible_after_chapter_id: UUID | None,
    first_appear_chapter_id: UUID | None,
    context: SpoilerContext,
    ranks: dict[UUID, int],
) -> bool:
    req = _required_rank(ranks, visible_after_chapter_id, first_appear_chapter_id)
    return is_visible(
        context=context,
        required_progress_rank=req,
        spoiler_level=spoiler_level,
    )


# ── chapter ───────────────────────────────────────────────────────────


def list_chapters(
    db: Session,
    *,
    context: SpoilerContext,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Chapter], str | None]:
    stmt = (
        select(Chapter)
        .where(Chapter.status == ContentStatus.PUBLISHED)
        .order_by(Chapter.created_at, Chapter.id)
    )
    return _visible_page(
        db,
        stmt=stmt,
        cursor=cursor,
        limit=limit,
        predicate=lambda chapter: chapter.progress_rank <= context.progress_rank,
    )


def get_chapter_by_slug(
    db: Session,
    slug: str,
    *,
    context: SpoilerContext,
) -> Chapter | None:
    chapter = db.scalar(
        select(Chapter).where(
            Chapter.slug == slug,
            Chapter.status == ContentStatus.PUBLISHED,
        )
    )
    if chapter is None or chapter.progress_rank > context.progress_rank:
        return None
    return chapter


# ── faction ───────────────────────────────────────────────────────────


def list_factions_published(
    db: Session,
    *,
    context: SpoilerContext,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Faction], str | None]:
    ranks = _chapter_rank_map(db)
    stmt = (
        select(Faction)
        .where(Faction.status == ContentStatus.PUBLISHED)
        .order_by(Faction.created_at, Faction.id)
    )
    return _visible_page(
        db,
        stmt=stmt,
        cursor=cursor,
        limit=limit,
        predicate=lambda faction: passes_spoiler(
            spoiler_level=faction.spoiler_level,
            visible_after_chapter_id=faction.visible_after_chapter_id,
            first_appear_chapter_id=None,
            context=context,
            ranks=ranks,
        ),
    )


def get_faction_by_slug_published(
    db: Session,
    slug: str,
    *,
    context: SpoilerContext,
) -> Faction | None:
    f = db.scalar(
        select(Faction).where(Faction.slug == slug, Faction.status == ContentStatus.PUBLISHED)
    )
    if f is None:
        return None
    ranks = _chapter_rank_map(db)
    if not passes_spoiler(
        spoiler_level=f.spoiler_level,
        visible_after_chapter_id=f.visible_after_chapter_id,
        first_appear_chapter_id=None,
        context=context,
        ranks=ranks,
    ):
        return None
    return f


# ── character ─────────────────────────────────────────────────────────


def list_characters_published(
    db: Session,
    *,
    context: SpoilerContext,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Character], str | None]:
    ranks = _chapter_rank_map(db)
    stmt = (
        select(Character)
        .where(Character.status == ContentStatus.PUBLISHED)
        .order_by(Character.created_at, Character.id)
    )
    return _visible_page(
        db,
        stmt=stmt,
        cursor=cursor,
        limit=limit,
        predicate=lambda character: passes_spoiler(
            spoiler_level=character.spoiler_level,
            visible_after_chapter_id=character.visible_after_chapter_id,
            first_appear_chapter_id=character.first_appear_chapter_id,
            context=context,
            ranks=ranks,
        ),
    )


def get_character_by_slug_published(
    db: Session,
    slug: str,
    *,
    context: SpoilerContext,
) -> Character | None:
    c = db.scalar(
        select(Character)
        .options(joinedload(Character.aliases))
        .where(Character.slug == slug, Character.status == ContentStatus.PUBLISHED)
    )
    if c is None:
        return None
    ranks = _chapter_rank_map(db)
    if not passes_spoiler(
        spoiler_level=c.spoiler_level,
        visible_after_chapter_id=c.visible_after_chapter_id,
        first_appear_chapter_id=c.first_appear_chapter_id,
        context=context,
        ranks=ranks,
    ):
        return None
    return c


# ── story event ───────────────────────────────────────────────────────


def list_events_published(
    db: Session,
    *,
    context: SpoilerContext,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[StoryEvent], str | None]:
    ranks = _chapter_rank_map(db)
    stmt = (
        select(StoryEvent)
        .where(StoryEvent.status == ContentStatus.PUBLISHED)
        .order_by(StoryEvent.created_at, StoryEvent.id)
    )
    return _visible_page(
        db,
        stmt=stmt,
        cursor=cursor,
        limit=limit,
        predicate=lambda event: passes_spoiler(
            spoiler_level=event.spoiler_level,
            visible_after_chapter_id=event.visible_after_chapter_id,
            first_appear_chapter_id=event.chapter_id,
            context=context,
            ranks=ranks,
        ),
    )


def get_event_by_slug_published(
    db: Session,
    slug: str,
    *,
    context: SpoilerContext,
) -> StoryEvent | None:
    e = db.scalar(
        select(StoryEvent).where(
            StoryEvent.slug == slug, StoryEvent.status == ContentStatus.PUBLISHED
        )
    )
    if e is None:
        return None
    ranks = _chapter_rank_map(db)
    if not passes_spoiler(
        spoiler_level=e.spoiler_level,
        visible_after_chapter_id=e.visible_after_chapter_id,
        first_appear_chapter_id=None,
        context=context,
        ranks=ranks,
    ):
        return None
    return e


# ── source (by id, never publicly listed) ─────────────────────────────


def get_source_by_id_published(
    db: Session,
    source_id: UUID,
    *,
    context: SpoilerContext,
) -> Source | None:
    source = db.get(Source, source_id)
    if source is None:
        return None
    ranks = _chapter_rank_map(db)
    if source.chapter_id:
        chapter = db.get(Chapter, source.chapter_id)
        if chapter is None or chapter.status != ContentStatus.PUBLISHED:
            return None
        visible = is_visible(
            context=context,
            required_progress_rank=chapter.progress_rank,
            spoiler_level=0,
        )
    elif source.faction_id:
        faction = db.get(Faction, source.faction_id)
        if faction is None or faction.status != ContentStatus.PUBLISHED:
            return None
        visible = passes_spoiler(
            spoiler_level=faction.spoiler_level,
            visible_after_chapter_id=faction.visible_after_chapter_id,
            first_appear_chapter_id=None,
            context=context,
            ranks=ranks,
        )
    elif source.character_id:
        character = db.get(Character, source.character_id)
        if character is None or character.status != ContentStatus.PUBLISHED:
            return None
        visible = passes_spoiler(
            spoiler_level=character.spoiler_level,
            visible_after_chapter_id=character.visible_after_chapter_id,
            first_appear_chapter_id=character.first_appear_chapter_id,
            context=context,
            ranks=ranks,
        )
    elif source.event_id:
        event = db.get(StoryEvent, source.event_id)
        if event is None or event.status != ContentStatus.PUBLISHED:
            return None
        visible = passes_spoiler(
            spoiler_level=event.spoiler_level,
            visible_after_chapter_id=event.visible_after_chapter_id,
            first_appear_chapter_id=event.chapter_id,
            context=context,
            ranks=ranks,
        )
    elif source.relationship_id:
        relationship = db.get(Relationship, source.relationship_id)
        if relationship is None or relationship.status != ContentStatus.PUBLISHED:
            return None
        visible = passes_spoiler(
            spoiler_level=relationship.spoiler_level,
            visible_after_chapter_id=relationship.visible_after_chapter_id,
            first_appear_chapter_id=relationship.chapter_id,
            context=context,
            ranks=ranks,
        )
    else:
        return None
    return source if visible else None


# ── generic write helpers (flush, no commit) ─────────────────────────


def flush_new(db: Session, obj: object) -> None:
    db.add(obj)
    db.flush()


def flush_delete(db: Session, obj: object) -> None:
    db.delete(obj)
    db.flush()
