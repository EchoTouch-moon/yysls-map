import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db import get_db
from app.domain import ContentStatus, ProgressKey, RelationType
from app.models import Chapter, Character, Faction, Relationship
from app.schemas import ApiResponse, GraphData, GraphEdge, GraphNode
from app.services.spoiler import context_for, is_visible

router = APIRouter(prefix="/graph", tags=["graph"])


def _chapter_rank_map(db: Session) -> dict[uuid.UUID, int]:
    return {
        chapter_id: progress_rank
        for chapter_id, progress_rank in db.execute(select(Chapter.id, Chapter.progress_rank)).all()
    }


@router.get("", response_model=ApiResponse[GraphData])
def get_graph(
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    chapter: str | None = None,
    faction: str | None = None,
    relation_type: RelationType | None = None,
    focus: str | None = None,
) -> ApiResponse[GraphData]:
    context = context_for(progress)
    ranks = _chapter_rank_map(db)

    character_query = (
        select(Character, Faction.name)
        .outerjoin(
            Faction,
            (Character.faction_id == Faction.id) & (Faction.status == ContentStatus.PUBLISHED),
        )
        .where(Character.status == ContentStatus.PUBLISHED)
    )
    if chapter:
        character_query = character_query.join(
            Chapter, Character.first_appear_chapter_id == Chapter.id
        ).where(
            Chapter.slug == chapter,
            Chapter.status == ContentStatus.PUBLISHED,
        )
    if faction:
        character_query = character_query.where(Faction.slug == faction)
    if focus:
        focus_id = db.scalar(
            select(Character.id).where(
                Character.slug == focus,
                Character.status == ContentStatus.PUBLISHED,
            )
        )
        if focus_id is None:
            return ApiResponse(data=GraphData(nodes=[], edges=[], progress=progress))
        endpoints = db.execute(
            select(
                Relationship.source_character_id,
                Relationship.target_character_id,
                Relationship.visible_after_chapter_id,
                Relationship.chapter_id,
                Relationship.spoiler_level,
            ).where(
                Relationship.status == ContentStatus.PUBLISHED,
                (Relationship.source_character_id == focus_id)
                | (Relationship.target_character_id == focus_id),
            )
        ).all()
        visible_ids = {focus_id}
        for source_id, target_id, visible_after_id, chapter_id, spoiler_level in endpoints:
            if is_visible(
                context=context,
                required_progress_rank=ranks.get(visible_after_id or chapter_id),
                spoiler_level=spoiler_level,
            ):
                visible_ids.update((source_id, target_id))
        character_query = character_query.where(Character.id.in_(visible_ids))

    nodes: list[GraphNode] = []
    visible_character_ids: set[uuid.UUID] = set()
    for character, faction_name in db.execute(character_query).all():
        required_rank = ranks.get(
            character.visible_after_chapter_id or character.first_appear_chapter_id
        )
        if not is_visible(
            context=context,
            required_progress_rank=required_rank,
            spoiler_level=character.spoiler_level,
        ):
            continue
        visible_character_ids.add(character.id)
        nodes.append(
            GraphNode(
                id=character.id,
                slug=character.slug,
                label=character.name,
                faction_id=character.faction_id,
                faction_name=faction_name,
                importance=character.importance,
                summary=character.summary,
            )
        )

    if not visible_character_ids:
        return ApiResponse(data=GraphData(nodes=[], edges=[], progress=progress))

    source_chapter = aliased(Chapter)
    relationship_query = (
        select(Relationship, source_chapter.progress_rank)
        .outerjoin(source_chapter, Relationship.visible_after_chapter_id == source_chapter.id)
        .where(
            Relationship.status == ContentStatus.PUBLISHED,
            Relationship.source_character_id.in_(visible_character_ids),
            Relationship.target_character_id.in_(visible_character_ids),
        )
    )
    if relation_type:
        relationship_query = relationship_query.where(Relationship.relation_type == relation_type)

    edges: list[GraphEdge] = []
    for relationship, required_rank in db.execute(relationship_query).all():
        if not is_visible(
            context=context,
            required_progress_rank=required_rank,
            spoiler_level=relationship.spoiler_level,
        ):
            continue
        edges.append(
            GraphEdge(
                id=relationship.id,
                source=relationship.source_character_id,
                target=relationship.target_character_id,
                relation_type=relationship.relation_type,
                label=relationship.label,
                summary=relationship.summary,
                directional=relationship.is_directional,
                confidence=float(relationship.confidence),
            )
        )

    return ApiResponse(data=GraphData(nodes=nodes, edges=edges, progress=progress))
