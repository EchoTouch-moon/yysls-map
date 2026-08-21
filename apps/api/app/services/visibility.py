"""Shared spoiler-visibility helpers for public API projections."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chapter
from app.services.spoiler import SpoilerContext, is_visible


def chapter_ranks(db: Session) -> dict[uuid.UUID, int]:
    return {
        chapter_id: progress_rank
        for chapter_id, progress_rank in db.execute(
            select(Chapter.id, Chapter.progress_rank)
        ).all()
    }


def visible_entity(
    *,
    context: SpoilerContext,
    ranks: dict[uuid.UUID, int],
    visible_after_chapter_id: uuid.UUID | None,
    spoiler_level: int,
) -> bool:
    return is_visible(
        context=context,
        required_progress_rank=(
            ranks.get(visible_after_chapter_id) if visible_after_chapter_id is not None else None
        ),
        spoiler_level=spoiler_level,
    )
