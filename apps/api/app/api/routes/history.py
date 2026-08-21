from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import (
    HistoricalReferenceRead,
    HistoryDetailRead,
    HistoryListData,
    HistoryListItem,
    RelatedBeatRef,
)
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import (
    Chapter,
    EventHistoricalLink,
    HistoricalContext,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
)
from app.schemas import ApiResponse, RestrictedData
from app.services.spoiler import context_for
from app.services.visibility import chapter_ranks, visible_entity

router = APIRouter(prefix="/history", tags=["history"])


def _visible_contexts(db: Session, progress: ProgressKey) -> list[HistoricalContext]:
    spoiler_context = context_for(progress)
    ranks = chapter_ranks(db)
    contexts = db.scalars(
        select(HistoricalContext)
        .where(HistoricalContext.status == ContentStatus.PUBLISHED)
        .order_by(HistoricalContext.title.asc(), HistoricalContext.id.asc())
    ).all()
    return [
        item
        for item in contexts
        if visible_entity(
            context=spoiler_context,
            ranks=ranks,
            visible_after_chapter_id=item.visible_after_chapter_id,
            spoiler_level=item.spoiler_level,
        )
    ]


@router.get("", response_model=ApiResponse[HistoryListData])
def list_history(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[HistoryListData]:
    items = [
        HistoryListItem(
            slug=item.slug,
            title=item.title,
            period_label=item.period_label,
            summary=item.summary,
            fact_kind=item.fact_kind,
        )
        for item in _visible_contexts(db, progress)
    ]
    return ApiResponse(data=HistoryListData(progress=progress, contexts=items))


@router.get("/{slug}", response_model=ApiResponse[HistoryDetailRead | RestrictedData])
def get_history(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[HistoryDetailRead | RestrictedData]:
    spoiler_context = context_for(progress)
    ranks = chapter_ranks(db)
    historical = db.scalar(
        select(HistoricalContext)
        .options(selectinload(HistoricalContext.references))
        .where(
            HistoricalContext.slug == slug,
            HistoricalContext.status == ContentStatus.PUBLISHED,
        )
    )
    if historical is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="历史背景不存在。")
    if not visible_entity(
        context=spoiler_context,
        ranks=ranks,
        visible_after_chapter_id=historical.visible_after_chapter_id,
        spoiler_level=historical.spoiler_level,
    ):
        required_chapter = db.get(Chapter, historical.visible_after_chapter_id)
        return ApiResponse(
            data=RestrictedData(
                required_progress=required_chapter.progress_key if required_chapter else None
            )
        )

    related_beats = db.execute(
        select(StoryArcBeat, StoryEvent, StoryArc)
        .join(EventHistoricalLink, EventHistoricalLink.event_id == StoryArcBeat.event_id)
        .join(StoryEvent, StoryArcBeat.event_id == StoryEvent.id)
        .join(StoryArc, StoryArcBeat.arc_id == StoryArc.id)
        .where(
            EventHistoricalLink.context_id == historical.id,
            EventHistoricalLink.status == ContentStatus.PUBLISHED,
            StoryArcBeat.status == ContentStatus.PUBLISHED,
            StoryEvent.status == ContentStatus.PUBLISHED,
            StoryArc.status == ContentStatus.PUBLISHED,
        )
        .order_by(StoryArc.title.asc(), StoryArcBeat.sort_order.asc())
    ).all()

    return ApiResponse(
        data=HistoryDetailRead(
            slug=historical.slug,
            title=historical.title,
            period_label=historical.period_label,
            summary=historical.summary,
            fact_kind=historical.fact_kind,
            boundary_note=historical.boundary_note,
            references=[
                HistoricalReferenceRead(
                    reference_type=reference.reference_type,
                    title=reference.title,
                    publisher=reference.publisher,
                    url=reference.url,
                    locator=reference.locator,
                )
                for reference in sorted(
                    historical.references, key=lambda item: (item.title, item.id)
                )
            ],
            related=[
                RelatedBeatRef(
                    arc_slug=arc.slug,
                    arc_title=arc.title,
                    event_slug=event.slug,
                    event_title=event.title,
                )
                for beat, event, arc in related_beats
            ],
        )
    )
