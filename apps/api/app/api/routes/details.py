import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import (
    CharacterDetail,
    EvidenceSource,
    HistoryChip,
    RelationshipDetail,
    StoryPathStep,
)
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import (
    Chapter,
    Character,
    EventHistoricalLink,
    Faction,
    Relationship,
    Source,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
)
from app.schemas import ApiResponse, RestrictedData
from app.services.spoiler import SpoilerContext, context_for, is_visible
from app.services.visibility import chapter_ranks, visible_entity

router = APIRouter(tags=["details"])


def _story_path(
    db: Session,
    *,
    character_id: uuid.UUID,
    context: SpoilerContext,
) -> list[StoryPathStep]:
    ranks = chapter_ranks(db)
    beat_query = (
        select(StoryArcBeat)
        .join(StoryEvent, StoryArcBeat.event_id == StoryEvent.id)
        .join(StoryArc, StoryArcBeat.arc_id == StoryArc.id)
        .options(
            selectinload(StoryArcBeat.arc),
            selectinload(StoryArcBeat.event).selectinload(StoryEvent.characters),
        )
        .where(
            StoryArcBeat.status == ContentStatus.PUBLISHED,
            StoryEvent.status == ContentStatus.PUBLISHED,
            StoryArc.status == ContentStatus.PUBLISHED,
            StoryEvent.characters.any(Character.id == character_id),
        )
        .order_by(
            StoryArc.title.asc(),
            StoryArc.id.asc(),
            StoryArcBeat.sort_order.asc(),
            StoryArcBeat.id.asc(),
        )
    )
    beats = [
        beat
        for beat in db.scalars(beat_query).unique().all()
        # 可见性闭包: Arc -> Beat -> Event 三层全部可见才允许进入投影,
        # 防止未发布/未来卷通过已发布子节点泄漏。
        if beat.arc.status is ContentStatus.PUBLISHED
        and visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=beat.arc.visible_after_chapter_id,
            spoiler_level=beat.arc.spoiler_level,
        )
        and visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=beat.visible_after_chapter_id,
            spoiler_level=beat.spoiler_level,
        )
        and visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=beat.event.visible_after_chapter_id or beat.event.chapter_id,
            spoiler_level=beat.event.spoiler_level,
        )
    ]
    if not beats:
        return []

    event_ids = [beat.event_id for beat in beats]
    history_by_event: dict[uuid.UUID, list[HistoryChip]] = {}
    link_query = (
        select(EventHistoricalLink)
        .options(selectinload(EventHistoricalLink.context))
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
        if not visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=link.visible_after_chapter_id,
            spoiler_level=link.spoiler_level,
        ) or not visible_entity(
            context=context,
            ranks=ranks,
            visible_after_chapter_id=historical.visible_after_chapter_id,
            spoiler_level=historical.spoiler_level,
        ):
            continue
        history_by_event.setdefault(link.event_id, []).append(
            HistoryChip(
                slug=historical.slug,
                title=historical.title,
                relation_kind=link.relation_kind,
            )
        )

    return [
        StoryPathStep(
            arc_slug=beat.arc.slug,
            arc_title=beat.arc.title,
            beat_sort_order=beat.sort_order,
            role=beat.role,
            guide=beat.guide,
            event_slug=beat.event.slug,
            event_title=beat.event.title,
            event_summary=beat.event.summary,
            why_it_matters=beat.why_it_matters,
            historical=history_by_event.get(beat.event_id, []),
        )
        for beat in beats
    ]


@router.get(
    "/characters/{slug}",
    response_model=ApiResponse[CharacterDetail | RestrictedData],
)
def character_detail(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    reveal: bool = Query(default=False),
) -> ApiResponse[CharacterDetail | RestrictedData]:
    row = db.execute(
        select(Character, Faction.name, Chapter)
        .outerjoin(
            Faction,
            (Character.faction_id == Faction.id) & (Faction.status == ContentStatus.PUBLISHED),
        )
        .outerjoin(
            Chapter,
            (Character.first_appear_chapter_id == Chapter.id)
            & (Chapter.status == ContentStatus.PUBLISHED),
        )
        .where(Character.slug == slug, Character.status == ContentStatus.PUBLISHED)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在。")
    character, faction_name, first_chapter = row
    required_chapter = db.get(
        Chapter, character.visible_after_chapter_id or character.first_appear_chapter_id
    )
    spoiler_context = context_for(progress, allow_reveal=reveal)
    visible = is_visible(
        context=spoiler_context,
        required_progress_rank=required_chapter.progress_rank if required_chapter else None,
        spoiler_level=character.spoiler_level,
    )
    if not visible:
        return ApiResponse(
            data=RestrictedData(
                required_progress=required_chapter.progress_key if required_chapter else None
            )
        )
    return ApiResponse(
        data=CharacterDetail(
            id=character.id,
            slug=character.slug,
            name=character.name,
            summary=character.summary,
            interpretation=character.interpretation,
            identity_tags=character.identity_tags,
            faction_name=faction_name,
            first_appear_chapter=first_chapter.title if first_chapter else None,
            sources=[
                EvidenceSource.model_validate(source)
                for source in db.scalars(
                    select(Source)
                    .where(Source.character_id == character.id)
                    .order_by(Source.title.asc())
                ).all()
            ],
            story_path=_story_path(db, character_id=character.id, context=spoiler_context),
        )
    )


@router.get(
    "/relationships/{relationship_id}",
    response_model=ApiResponse[RelationshipDetail | RestrictedData],
)
def relationship_detail(
    relationship_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    reveal: bool = Query(default=False),
) -> ApiResponse[RelationshipDetail | RestrictedData]:
    relationship = db.get(Relationship, relationship_id)
    if (
        relationship is None
        or relationship.status is not ContentStatus.PUBLISHED
        or relationship.source.status is not ContentStatus.PUBLISHED
        or relationship.target.status is not ContentStatus.PUBLISHED
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关系不存在。")
    required_chapter = db.get(
        Chapter, relationship.visible_after_chapter_id or relationship.chapter_id
    )
    visible = is_visible(
        context=context_for(progress, allow_reveal=reveal),
        required_progress_rank=required_chapter.progress_rank if required_chapter else None,
        spoiler_level=relationship.spoiler_level,
    )
    if not visible:
        return ApiResponse(
            data=RestrictedData(
                required_progress=required_chapter.progress_key if required_chapter else None
            )
        )
    return ApiResponse(
        data=RelationshipDetail(
            id=relationship.id,
            source_name=relationship.source.name,
            target_name=relationship.target.name,
            relation_type=relationship.relation_type,
            label=relationship.label,
            summary=relationship.summary,
            stage=relationship.stage,
            confidence=float(Decimal(relationship.confidence)),
            sources=[
                EvidenceSource.model_validate(source)
                for source in db.scalars(
                    select(Source)
                    .where(Source.relationship_id == relationship.id)
                    .order_by(Source.title.asc())
                ).all()
            ],
        )
    )
