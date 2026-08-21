import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import EvidenceSource, TimelineCharacter, TimelineData, TimelineEvent
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import Chapter, Source, StoryEvent
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

    visible_events: list[StoryEvent] = []
    for event in db.scalars(query).unique().all():
        required_chapter = db.get(Chapter, event.visible_after_chapter_id or event.chapter_id)
        if not is_visible(
            context=context,
            required_progress_rank=required_chapter.progress_rank if required_chapter else None,
            spoiler_level=event.spoiler_level,
        ):
            continue
        visible_events.append(event)

    sources_by_event: dict[uuid.UUID, list[EvidenceSource]] = {}
    if visible_events:
        for source in db.scalars(
            select(Source)
            .where(Source.event_id.in_([event.id for event in visible_events]))
            .order_by(Source.title.asc())
        ).all():
            if source.event_id is not None:
                sources_by_event.setdefault(source.event_id, []).append(
                    EvidenceSource.model_validate(source)
                )

    events = [
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
            sources=sources_by_event.get(event.id, []),
        )
        for event in visible_events
    ]
    return ApiResponse(data=TimelineData(progress=progress, events=events))
