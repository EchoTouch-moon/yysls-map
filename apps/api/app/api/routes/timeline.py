import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import (
    CanonicalEventBeatOverlay,
    CanonicalEventOverlay,
    CanonicalNodeRead,
    EvidenceSource,
    HistoricalContextRead,
    HistoricalReferenceRead,
    StoryArcRelationship,
    TimelineCanonicalChapter,
    TimelineCanonicalData,
    TimelineCharacter,
    TimelineData,
    TimelineEvent,
)
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import (
    CanonicalStoryEventLink,
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
from app.services.canonical import ordered_main_spine
from app.services.spoiler import SpoilerContext, context_for, is_visible
from app.services.visibility import chapter_ranks, visible_entity

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



def _event_overlay(
    db: Session,
    *,
    event: StoryEvent,
    mapping_kind: object,
    context: SpoilerContext,
    ranks: dict[uuid.UUID, int],
    beat: StoryArcBeat | None,
    sources_by_event: dict[uuid.UUID, list[EvidenceSource]],
    relationships_by_event: dict[uuid.UUID, list[StoryArcRelationship]],
    history_by_event: dict[uuid.UUID, list[HistoricalContextRead]],
) -> CanonicalEventOverlay:
    visible_characters = [
        TimelineCharacter(slug=character.slug, name=character.name)
        for character in sorted(event.characters, key=lambda item: (item.name, item.id))
        if character.status is ContentStatus.PUBLISHED
        and visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=(
                character.visible_after_chapter_id or character.first_appear_chapter_id
            ),
            spoiler_level=character.spoiler_level,
        )
    ]
    return CanonicalEventOverlay(
        mapping_kind=mapping_kind,
        slug=event.slug,
        title=event.title,
        summary=event.summary,
        impact=event.impact,
        chapter_slug=event.chapter.slug,
        chapter_title=event.chapter.title,
        characters=visible_characters,
        sources=sources_by_event.get(event.id, []),
        relationships=relationships_by_event.get(event.id, []),
        historical_contexts=history_by_event.get(event.id, []),
        beat=(
            CanonicalEventBeatOverlay(
                role=beat.role,
                guide=beat.guide,
                why_it_matters=beat.why_it_matters,
                bridge=beat.bridge,
                next_question=beat.next_question,
            )
            if beat is not None
            else None
        ),
    )


@router.get("/canonical", response_model=ApiResponse[TimelineCanonicalData])
def get_timeline_canonical(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    chapter: str = "qinghe",
) -> ApiResponse[TimelineCanonicalData]:
    """Canonical-first main spine for one chapter (Phase D, D-G1..D-G5).

    - Order comes only from canonical hierarchy + sort_order (never beats);
    - editorial overlays (StoryEvent/beat/history/characters) are attached per
      node and never reorder the spine;
    - zero-link canonical nodes are still returned (coverage-safe, D-G4);
    - visibility closure: nodes only surface once the chapter is unlocked, and
      each event overlay only when that event is visible (D-G5).
    """
    context = context_for(progress)
    ranks = chapter_ranks(db)
    chapter_row = db.scalar(select(Chapter).where(Chapter.slug == chapter))
    if chapter_row is None:
        return ApiResponse(
            data=TimelineCanonicalData(
                progress=progress,
                chapter=None,
                chapter_unlocked=False,
            )
        )
    unlocked = is_visible(
        context=context,
        required_progress_rank=chapter_row.progress_rank,
        spoiler_level=0,
    )
    chapter_read = TimelineCanonicalChapter(
        slug=chapter_row.slug,
        title=chapter_row.title,
        region=chapter_row.region,
    )
    if not unlocked:
        return ApiResponse(
            data=TimelineCanonicalData(
                progress=progress,
                chapter=chapter_read,
                chapter_unlocked=False,
            )
        )

    spine_nodes = ordered_main_spine(
        db, chapter_slug=chapter, status=ContentStatus.PUBLISHED
    )
    node_ids = [node.id for node in spine_nodes]

    links = (
        db.scalars(
            select(CanonicalStoryEventLink).where(
                CanonicalStoryEventLink.canonical_node_id.in_(node_ids)
            )
        ).unique().all()
        if node_ids
        else []
    )
    linked_event_ids = {link.story_event_id for link in links}
    events = (
        db.scalars(
            select(StoryEvent)
            .options(
                selectinload(StoryEvent.characters),
                selectinload(StoryEvent.chapter),
            )
            .where(
                StoryEvent.id.in_(linked_event_ids),
                StoryEvent.status == ContentStatus.PUBLISHED,
            )
        ).unique().all()
        if linked_event_ids
        else []
    )
    event_by_id = {event.id: event for event in events}
    visible_event_ids = [
        event.id
        for event in events
        if visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=event.visible_after_chapter_id or event.chapter_id,
            spoiler_level=event.spoiler_level,
        )
    ]
    visible_event_by_id = {
        event_id: event_by_id[event_id] for event_id in visible_event_ids
    }

    # editorial beat overlays (published arc chain only)
    beats = (
        db.scalars(
            select(StoryArcBeat)
            .join(StoryArc, StoryArcBeat.arc_id == StoryArc.id)
            .options(selectinload(StoryArcBeat.arc))
            .where(
                StoryArcBeat.event_id.in_(linked_event_ids),
                StoryArcBeat.status == ContentStatus.PUBLISHED,
                StoryArc.status == ContentStatus.PUBLISHED,
            )
            .order_by(StoryArc.title.asc(), StoryArc.id.asc(), StoryArcBeat.sort_order.asc())
        ).unique().all()
        if linked_event_ids
        else []
    )
    beat_by_event: dict[uuid.UUID, StoryArcBeat] = {}
    for beat in beats:
        if (
            beat.event_id not in beat_by_event
            and visible_entity(
                context=context,
                ranks=ranks,
                visible_after_chapter_id=beat.arc.visible_after_chapter_id,
                spoiler_level=beat.arc.spoiler_level,
            )
        ):
            beat_by_event[beat.event_id] = beat

    sources_by_event: dict[uuid.UUID, list[EvidenceSource]] = {}
    if linked_event_ids:
        for source in db.scalars(
            select(Source)
            .where(
                Source.event_id.in_(linked_event_ids),
                Source.event_id.is_not(None),
            )
            .order_by(Source.title.asc(), Source.id.asc())
        ).all():
            if source.event_id is not None:
                sources_by_event.setdefault(source.event_id, []).append(
                    EvidenceSource.model_validate(source)
                )

    relationships_by_event: dict[uuid.UUID, list[StoryArcRelationship]] = {}
    if linked_event_ids:
        relationship_query = (
            select(Relationship)
            .options(
                selectinload(Relationship.events),
                selectinload(Relationship.source),
                selectinload(Relationship.target),
            )
            .where(
                Relationship.status == ContentStatus.PUBLISHED,
                Relationship.events.any(StoryEvent.id.in_(linked_event_ids)),
            )
            .order_by(Relationship.label.asc(), Relationship.id.asc())
        )
        for relationship in db.scalars(relationship_query).unique().all():
            if not visible_entity(
                context=context,
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
                or not visible_entity(
                    context=context,
                    ranks=ranks,
                    visible_after_chapter_id=(
                        character.visible_after_chapter_id
                        or character.first_appear_chapter_id
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
                if event.id in linked_event_ids:
                    relationships_by_event.setdefault(event.id, []).append(item)

    history_by_event: dict[uuid.UUID, list[HistoricalContextRead]] = {}
    if linked_event_ids:
        link_query = (
            select(EventHistoricalLink)
            .options(
                selectinload(EventHistoricalLink.context).selectinload(
                    HistoricalContext.references
                )
            )
            .where(
                EventHistoricalLink.event_id.in_(linked_event_ids),
                EventHistoricalLink.status == ContentStatus.PUBLISHED,
            )
            .order_by(EventHistoricalLink.sort_order.asc(), EventHistoricalLink.id.asc())
        )
        for history_link in db.scalars(link_query).unique().all():
            historical = history_link.context
            if historical.status is not ContentStatus.PUBLISHED:
                continue
            if not visible_entity(
                context=context,
                ranks=ranks,
                visible_after_chapter_id=history_link.visible_after_chapter_id,
                spoiler_level=history_link.spoiler_level,
            ) or not visible_entity(
                context=context,
                ranks=ranks,
                visible_after_chapter_id=historical.visible_after_chapter_id,
                spoiler_level=historical.spoiler_level,
            ):
                continue
            history_by_event.setdefault(history_link.event_id, []).append(
                HistoricalContextRead(
                    id=historical.id,
                    slug=historical.slug,
                    title=historical.title,
                    period_label=historical.period_label,
                    summary=historical.summary,
                    fact_kind=historical.fact_kind,
                    boundary_note=historical.boundary_note,
                    relation_kind=history_link.relation_kind,
                    editorial_note=history_link.editorial_note,
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

    links_by_node: dict[uuid.UUID, list[CanonicalStoryEventLink]] = {}
    node_key_by_id: dict[uuid.UUID, str] = {}
    for node in spine_nodes:
        node_key_by_id[node.id] = node.canonical_key
    for link in links:
        links_by_node.setdefault(link.canonical_node_id, []).append(link)

    spine = []
    for node in spine_nodes:
        node_events = []
        for node_link in sorted(
            links_by_node.get(node.id, []),
            key=lambda item: (item.sort_order, item.id),
        ):
            node_event = visible_event_by_id.get(node_link.story_event_id)
            if node_event is None:
                continue
            node_events.append(
                _event_overlay(
                    db,
                    event=node_event,
                    mapping_kind=node_link.mapping_kind,
                    context=context,
                    ranks=ranks,
                    beat=beat_by_event.get(node_event.id),
                    sources_by_event=sources_by_event,
                    relationships_by_event=relationships_by_event,
                    history_by_event=history_by_event,
                )
            )
        spine.append(
            CanonicalNodeRead(
                canonical_key=node.canonical_key,
                title=node.title,
                node_type=node.node_type,
                parent_key=(
                    node_key_by_id[node.parent_id] if node.parent_id is not None else None
                ),
                sort_order=node.sort_order,
                events=node_events,
            )
        )

    # beat_index: every link, so ?beat= bridges to canonical nodes (D-G6)
    beat_index: dict[str, list[str]] = {}
    for index_link in links:
        index_event = event_by_id.get(index_link.story_event_id)
        node_key = node_key_by_id.get(index_link.canonical_node_id)
        if index_event is not None and node_key is not None:
            beat_index.setdefault(index_event.slug, []).append(node_key)

    # unplaced events: visible chapter events without any canonical link
    # (editorial-only interpretation, e.g. wangqing-battle) for deep-link fallback.
    unplaced_events: list[CanonicalEventOverlay] = []
    all_chapter_events = (
        db.scalars(
            select(StoryEvent)
            .options(
                selectinload(StoryEvent.characters),
                selectinload(StoryEvent.chapter),
            )
            .where(
                StoryEvent.chapter_id == chapter_row.id,
                StoryEvent.status == ContentStatus.PUBLISHED,
            )
        ).unique().all()
    )
    for event in all_chapter_events:
        if event.id in linked_event_ids:
            continue
        if not visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=event.visible_after_chapter_id or event.chapter_id,
            spoiler_level=event.spoiler_level,
        ):
            continue
        unplaced_events.append(
            _event_overlay(
                db,
                event=event,
                mapping_kind=None,
                context=context,
                ranks=ranks,
                beat=beat_by_event.get(event.id),
                sources_by_event=sources_by_event,
                relationships_by_event=relationships_by_event,
                history_by_event=history_by_event,
            )
        )

    return ApiResponse(
        data=TimelineCanonicalData(
            progress=progress,
            chapter=chapter_read,
            chapter_unlocked=True,
            spine=spine,
            beat_index=beat_index,
            unplaced_events=unplaced_events,
        )
    )
