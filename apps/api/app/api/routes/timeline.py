from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import TimelineCharacter, TimelineData, TimelineEvent
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import Chapter, StoryEvent
from app.schemas import ApiResponse
from app.services.spoiler import context_for, is_visible

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("", response_model=ApiResponse[TimelineData])
def get_timeline(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    chapter: str | None = None,
) -> ApiResponse[TimelineData]:
    context = context_for(progress)
    query = (
        select(StoryEvent)
        .join(Chapter, StoryEvent.chapter_id == Chapter.id)
        .options(selectinload(StoryEvent.characters))
        .where(StoryEvent.status == ContentStatus.PUBLISHED)
        .order_by(Chapter.sort_order.asc(), StoryEvent.sort_order.asc())
    )
    if chapter:
        query = query.where(Chapter.slug == chapter)

    events: list[TimelineEvent] = []
    for event in db.scalars(query).unique().all():
        required_chapter = db.get(
            Chapter, event.visible_after_chapter_id or event.chapter_id
        )
        if not is_visible(
            context=context,
            required_progress_rank=required_chapter.progress_rank if required_chapter else None,
            spoiler_level=event.spoiler_level,
        ):
            continue
        events.append(
            TimelineEvent(
                id=event.id,
                slug=event.slug,
                title=event.title,
                summary=event.summary,
                impact=event.impact,
                chapter_slug=event.chapter.slug,
                chapter_title=event.chapter.title,
                sort_order=event.sort_order,
                characters=[
                    TimelineCharacter(slug=character.slug, name=character.name)
                    for character in event.characters
                ],
            )
        )
    return ApiResponse(data=TimelineData(progress=progress, events=events))

