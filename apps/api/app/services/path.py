import uuid
from collections import defaultdict, deque
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import PathEdge, PathNode, RelationshipPathData
from app.domain import ContentStatus, ProgressKey
from app.models import Chapter, Character, Relationship
from app.services.spoiler import context_for, is_visible


@dataclass(frozen=True)
class TraversalEdge:
    relationship: Relationship
    other_id: uuid.UUID


def shortest_visible_path(
    db: Session,
    *,
    source_slug: str,
    target_slug: str,
    progress: ProgressKey,
    max_depth: int = 6,
    max_visited: int = 1000,
) -> RelationshipPathData:
    endpoints = db.scalars(
        select(Character).where(
            Character.slug.in_([source_slug, target_slug]),
            Character.status == ContentStatus.PUBLISHED,
        )
    ).all()
    by_slug = {character.slug: character for character in endpoints}
    source = by_slug.get(source_slug)
    target = by_slug.get(target_slug)
    if source is None or target is None:
        return RelationshipPathData(found=False, nodes=[], edges=[])
    if source.id == target.id:
        return RelationshipPathData(
            found=True,
            nodes=[PathNode(id=source.id, slug=source.slug, name=source.name)],
            edges=[],
        )

    ranks = {
        chapter_id: rank
        for chapter_id, rank in db.execute(select(Chapter.id, Chapter.progress_rank)).all()
    }
    context = context_for(progress)
    visible_characters: dict[uuid.UUID, Character] = {}
    for character in db.scalars(
        select(Character).where(Character.status == ContentStatus.PUBLISHED)
    ):
        required_rank = ranks.get(
            character.visible_after_chapter_id or character.first_appear_chapter_id
        )
        if is_visible(
            context=context,
            required_progress_rank=required_rank,
            spoiler_level=character.spoiler_level,
        ):
            visible_characters[character.id] = character

    if source.id not in visible_characters or target.id not in visible_characters:
        return RelationshipPathData(found=False, nodes=[], edges=[])

    adjacency: dict[uuid.UUID, list[TraversalEdge]] = defaultdict(list)
    for relationship in db.scalars(
        select(Relationship).where(Relationship.status == ContentStatus.PUBLISHED)
    ):
        if (
            relationship.source_character_id not in visible_characters
            or relationship.target_character_id not in visible_characters
        ):
            continue
        required_rank = ranks.get(
            relationship.visible_after_chapter_id or relationship.chapter_id
        )
        if not is_visible(
            context=context,
            required_progress_rank=required_rank,
            spoiler_level=relationship.spoiler_level,
        ):
            continue
        adjacency[relationship.source_character_id].append(
            TraversalEdge(relationship=relationship, other_id=relationship.target_character_id)
        )
        adjacency[relationship.target_character_id].append(
            TraversalEdge(relationship=relationship, other_id=relationship.source_character_id)
        )

    queue: deque[tuple[uuid.UUID, int]] = deque([(source.id, 0)])
    visited = {source.id}
    previous: dict[uuid.UUID, tuple[uuid.UUID, Relationship]] = {}

    while queue and len(visited) <= max_visited:
        current_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for traversal in adjacency[current_id]:
            if traversal.other_id in visited:
                continue
            visited.add(traversal.other_id)
            previous[traversal.other_id] = (current_id, traversal.relationship)
            if traversal.other_id == target.id:
                queue.clear()
                break
            queue.append((traversal.other_id, depth + 1))

    if target.id not in previous:
        return RelationshipPathData(found=False, nodes=[], edges=[])

    node_ids = [target.id]
    relationships: list[Relationship] = []
    cursor = target.id
    while cursor != source.id:
        parent, relationship = previous[cursor]
        relationships.append(relationship)
        node_ids.append(parent)
        cursor = parent
    node_ids.reverse()
    relationships.reverse()

    return RelationshipPathData(
        found=True,
        nodes=[
            PathNode(
                id=character_id,
                slug=visible_characters[character_id].slug,
                name=visible_characters[character_id].name,
            )
            for character_id in node_ids
        ],
        edges=[
            PathEdge(
                id=relationship.id,
                source=relationship.source_character_id,
                target=relationship.target_character_id,
                label=relationship.label,
                relation_type=relationship.relation_type,
            )
            for relationship in relationships
        ],
    )

