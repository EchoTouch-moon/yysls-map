import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import (
    EvidenceSource,
    HistoricalContextRead,
    HistoricalReferenceRead,
    StoryArcBeatEvent,
    StoryArcBeatRead,
    StoryArcDetail,
    StoryArcListData,
    StoryArcListItem,
    StoryArcRelationship,
    TimelineCharacter,
)
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import (
    Chapter,
    EventHistoricalLink,
    HistoricalContext,
    Relationship,
    Source,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
)
from app.schemas import ApiResponse
from app.services.spoiler import SpoilerContext, context_for, is_visible

router = APIRouter(prefix="/story-arcs", tags=["story-arcs"])


def _chapter_ranks(db: Session) -> dict[uuid.UUID, int]:
    return {
        chapter_id: progress_rank
        for chapter_id, progress_rank in db.execute(select(Chapter.id, Chapter.progress_rank)).all()
    }


def _visible(
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


def _visible_beat(
    beat: StoryArcBeat,
    *,
    context: SpoilerContext,
    ranks: dict[uuid.UUID, int],
) -> bool:
    event = beat.event
    return (
        beat.status is ContentStatus.PUBLISHED
        and event.status is ContentStatus.PUBLISHED
        and _visible(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=beat.visible_after_chapter_id,
            spoiler_level=beat.spoiler_level,
        )
        and _visible(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=event.visible_after_chapter_id or event.chapter_id,
            spoiler_level=event.spoiler_level,
        )
    )


def _arc_query() -> Select[tuple[StoryArc]]:
    return (
        select(StoryArc)
        .options(
            selectinload(StoryArc.beats)
            .selectinload(StoryArcBeat.event)
            .selectinload(StoryEvent.characters),
            selectinload(StoryArc.beats)
            .selectinload(StoryArcBeat.event)
            .selectinload(StoryEvent.chapter),
        )
        .where(StoryArc.status == ContentStatus.PUBLISHED)
        .order_by(StoryArc.title.asc(), StoryArc.id.asc())
    )


@router.get("", response_model=ApiResponse[StoryArcListData])
def list_story_arcs(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[StoryArcListData]:
    spoiler_context = context_for(progress)
    ranks = _chapter_ranks(db)
    arcs: list[StoryArcListItem] = []
    for arc in db.scalars(_arc_query()).unique().all():
        if not _visible(
            context=spoiler_context,
            ranks=ranks,
            visible_after_chapter_id=arc.visible_after_chapter_id,
            spoiler_level=arc.spoiler_level,
        ):
            continue
        arcs.append(
            StoryArcListItem(
                id=arc.id,
                slug=arc.slug,
                title=arc.title,
                summary=arc.summary,
                core_question=arc.core_question,
                estimated_minutes=arc.estimated_minutes,
                beat_count=sum(
                    _visible_beat(beat, context=spoiler_context, ranks=ranks) for beat in arc.beats
                ),
            )
        )
    return ApiResponse(data=StoryArcListData(progress=progress, arcs=arcs))


@router.get("/{slug}", response_model=ApiResponse[StoryArcDetail])
def get_story_arc(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[StoryArcDetail]:
    spoiler_context = context_for(progress)
    ranks = _chapter_ranks(db)
    arc = db.scalar(_arc_query().where(StoryArc.slug == slug))
    if arc is None or not _visible(
        context=spoiler_context,
        ranks=ranks,
        visible_after_chapter_id=arc.visible_after_chapter_id,
        spoiler_level=arc.spoiler_level,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="故事导读不存在。")

    visible_beats = sorted(
        (beat for beat in arc.beats if _visible_beat(beat, context=spoiler_context, ranks=ranks)),
        key=lambda beat: (beat.sort_order, beat.id),
    )
    event_ids = [beat.event_id for beat in visible_beats]

    sources_by_event: dict[uuid.UUID, list[EvidenceSource]] = {}
    if event_ids:
        for source in db.scalars(
            select(Source)
            .where(Source.event_id.in_(event_ids))
            .order_by(Source.title.asc(), Source.id.asc())
        ).all():
            if source.event_id is not None:
                sources_by_event.setdefault(source.event_id, []).append(
                    EvidenceSource.model_validate(source)
                )

    historical_by_event: dict[uuid.UUID, list[HistoricalContextRead]] = {}
    if event_ids:
        link_query = (
            select(EventHistoricalLink)
            .options(
                selectinload(EventHistoricalLink.context).selectinload(HistoricalContext.references)
            )
            .where(
                EventHistoricalLink.event_id.in_(event_ids),
                EventHistoricalLink.status == ContentStatus.PUBLISHED,
            )
            .order_by(EventHistoricalLink.sort_order.asc(), EventHistoricalLink.id.asc())
        )
        for link in db.scalars(link_query).unique().all():
            historical = link.context
            if historical.status is not ContentStatus.PUBLISHED:
                continue
            if not _visible(
                context=spoiler_context,
                ranks=ranks,
                visible_after_chapter_id=link.visible_after_chapter_id,
                spoiler_level=link.spoiler_level,
            ) or not _visible(
                context=spoiler_context,
                ranks=ranks,
                visible_after_chapter_id=historical.visible_after_chapter_id,
                spoiler_level=historical.spoiler_level,
            ):
                continue
            historical_by_event.setdefault(link.event_id, []).append(
                HistoricalContextRead(
                    id=historical.id,
                    slug=historical.slug,
                    title=historical.title,
                    period_label=historical.period_label,
                    summary=historical.summary,
                    fact_kind=historical.fact_kind,
                    boundary_note=historical.boundary_note,
                    relation_kind=link.relation_kind,
                    editorial_note=link.editorial_note,
                    references=[
                        HistoricalReferenceRead(
                            reference_type=reference.reference_type,
                            title=reference.title,
                            publisher=reference.publisher,
                            url=reference.url,
                            locator=reference.locator,
                        )
                        for reference in sorted(
                            historical.references,
                            key=lambda item: (item.title, item.id),
                        )
                    ],
                )
            )

    relationships_by_event: dict[uuid.UUID, list[StoryArcRelationship]] = {}
    if event_ids:
        relationship_query = (
            select(Relationship)
            .options(
                selectinload(Relationship.events),
                selectinload(Relationship.source),
                selectinload(Relationship.target),
            )
            .where(
                Relationship.status == ContentStatus.PUBLISHED,
                Relationship.events.any(StoryEvent.id.in_(event_ids)),
            )
            .order_by(Relationship.label.asc(), Relationship.id.asc())
        )
        for relationship in db.scalars(relationship_query).unique().all():
            if not _visible(
                context=spoiler_context,
                ranks=ranks,
                visible_after_chapter_id=(
                    relationship.visible_after_chapter_id or relationship.chapter_id
                ),
                spoiler_level=relationship.spoiler_level,
            ):
                continue
            endpoints = (relationship.source, relationship.target)
            if any(
                character.status is not ContentStatus.PUBLISHED
                or not _visible(
                    context=spoiler_context,
                    ranks=ranks,
                    visible_after_chapter_id=(
                        character.visible_after_chapter_id or character.first_appear_chapter_id
                    ),
                    spoiler_level=character.spoiler_level,
                )
                for character in endpoints
            ):
                continue
            item = StoryArcRelationship(
                id=relationship.id,
                relation_type=relationship.relation_type,
                label=relationship.label,
                source_slug=relationship.source.slug,
                source_name=relationship.source.name,
                target_slug=relationship.target.slug,
                target_name=relationship.target.name,
            )
            for event in relationship.events:
                if event.id in event_ids:
                    relationships_by_event.setdefault(event.id, []).append(item)

    beats: list[StoryArcBeatRead] = []
    for beat in visible_beats:
        event = beat.event
        visible_characters = [
            character
            for character in event.characters
            if character.status is ContentStatus.PUBLISHED
            and _visible(
                context=spoiler_context,
                ranks=ranks,
                visible_after_chapter_id=(
                    character.visible_after_chapter_id or character.first_appear_chapter_id
                ),
                spoiler_level=character.spoiler_level,
            )
        ]
        beats.append(
            StoryArcBeatRead(
                id=beat.id,
                sort_order=beat.sort_order,
                role=beat.role,
                guide=beat.guide,
                why_it_matters=beat.why_it_matters,
                bridge=beat.bridge,
                next_question=beat.next_question,
                event=StoryArcBeatEvent(
                    id=event.id,
                    slug=event.slug,
                    title=event.title,
                    summary=event.summary,
                    impact=event.impact,
                    chapter_slug=event.chapter.slug,
                    chapter_title=event.chapter.title,
                    characters=[
                        TimelineCharacter(slug=character.slug, name=character.name)
                        for character in sorted(
                            visible_characters, key=lambda item: (item.name, item.id)
                        )
                    ],
                    sources=sources_by_event.get(event.id, []),
                ),
                relationships=relationships_by_event.get(event.id, []),
                historical_contexts=historical_by_event.get(event.id, []),
            )
        )

    return ApiResponse(
        data=StoryArcDetail(
            id=arc.id,
            slug=arc.slug,
            title=arc.title,
            summary=arc.summary,
            core_question=arc.core_question,
            estimated_minutes=arc.estimated_minutes,
            progress=progress,
            beats=beats,
        )
    )
