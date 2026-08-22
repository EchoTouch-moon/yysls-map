"""Internal query helpers for the canonical story layer (frozen contract v0.1).

Deliberately minimal: C2 proves migration -> import -> validate -> query
internally. No public-facing /canonical-story API in this phase.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain import CanonicalSpine, CanonicalVerificationState, ContentStatus
from app.models import CanonicalStoryEventLink, CanonicalStoryNode


def get_canonical_node(db: Session, canonical_key: str) -> CanonicalStoryNode | None:
    return db.scalar(
        select(CanonicalStoryNode).where(
            CanonicalStoryNode.canonical_key == canonical_key
        )
    )


def list_canonical_nodes(
    db: Session,
    *,
    chapter_slug: str | None = None,
    spine: CanonicalSpine | None = None,
    status: ContentStatus | None = None,
    verification_state: CanonicalVerificationState | None = None,
) -> list[CanonicalStoryNode]:
    query = select(CanonicalStoryNode).order_by(
        CanonicalStoryNode.parent_id.asc(),
        CanonicalStoryNode.sort_order.asc(),
        CanonicalStoryNode.canonical_key.asc(),
    )
    if chapter_slug is not None:
        query = query.where(CanonicalStoryNode.chapter_slug == chapter_slug)
    if spine is not None:
        query = query.where(CanonicalStoryNode.spine == spine)
    if status is not None:
        query = query.where(CanonicalStoryNode.status == status)
    if verification_state is not None:
        query = query.where(CanonicalStoryNode.verification_state == verification_state)
    return list(db.scalars(query).unique().all())


def children_of(db: Session, node_id: uuid.UUID) -> list[CanonicalStoryNode]:
    return list(
        db.scalars(
            select(CanonicalStoryNode)
            .where(CanonicalStoryNode.parent_id == node_id)
            .order_by(CanonicalStoryNode.sort_order.asc(), CanonicalStoryNode.canonical_key.asc())
        ).unique().all()
    )


def get_links_for_node(
    db: Session, node_id: uuid.UUID
) -> list[CanonicalStoryEventLink]:
    return list(
        db.scalars(
            select(CanonicalStoryEventLink)
            .options(selectinload(CanonicalStoryEventLink.event))
            .where(CanonicalStoryEventLink.canonical_node_id == node_id)
            .order_by(
                CanonicalStoryEventLink.sort_order.asc(),
                CanonicalStoryEventLink.id.asc(),
            )
        ).unique().all()
    )


def get_links_for_event(
    db: Session, event_id: uuid.UUID
) -> list[CanonicalStoryEventLink]:
    return list(
        db.scalars(
            select(CanonicalStoryEventLink)
            .options(selectinload(CanonicalStoryEventLink.node))
            .where(CanonicalStoryEventLink.story_event_id == event_id)
            .order_by(
                CanonicalStoryEventLink.sort_order.asc(),
                CanonicalStoryEventLink.id.asc(),
            )
        ).unique().all()
    )


def ordered_main_spine(
    db: Session,
    *,
    chapter_slug: str,
    status: ContentStatus | None = ContentStatus.PUBLISHED,
) -> list[CanonicalStoryNode]:
    """Main-line nodes in reading order (hierarchy + sort_order, derived order).

    previous/next are never stored; this traversal is the single derivation.
    """
    nodes = list_canonical_nodes(
        db, chapter_slug=chapter_slug, spine=CanonicalSpine.MAIN, status=status
    )
    children: dict[uuid.UUID | None, list[CanonicalStoryNode]] = {}
    for node in nodes:
        children.setdefault(node.parent_id, []).append(node)
    for bucket in children.values():
        bucket.sort(key=lambda node: (node.sort_order, node.canonical_key))

    ordered: list[CanonicalStoryNode] = []

    def visit(node: CanonicalStoryNode) -> None:
        ordered.append(node)
        for child in children.get(node.id, []):
            visit(child)

    for root in children.get(None, []):
        visit(root)
    return ordered
