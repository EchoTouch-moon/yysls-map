import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.contracts import (
    AdminChapterRead,
    AdminChapterWrite,
    AdminCharacterRead,
    AdminCharacterWrite,
    AdminContentBootstrap,
    AdminEventRead,
    AdminEventWrite,
    AdminFactionRead,
    AdminFactionWrite,
    AdminRelationshipRead,
    AdminRelationshipWrite,
    ArchiveResult,
)
from app.domain import ContentStatus
from app.models import Chapter, Character, Faction, Relationship, StoryEvent


def _not_found(label: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{label}不存在。",
    )


def _invalid_reference(label: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"{label}包含不存在的引用。",
    )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="内容与现有 slug、排序或关系约束冲突。",
        ) from exc


def _require_chapter(db: Session, row_id: uuid.UUID | None) -> Chapter | None:
    if row_id is None:
        return None
    row = db.get(Chapter, row_id)
    if row is None:
        raise _invalid_reference("章节")
    return row


def _require_faction(db: Session, row_id: uuid.UUID | None) -> Faction | None:
    if row_id is None:
        return None
    row = db.get(Faction, row_id)
    if row is None:
        raise _invalid_reference("势力")
    return row


def _require_characters(db: Session, row_ids: Sequence[uuid.UUID]) -> list[Character]:
    unique_ids = set(row_ids)
    rows = list(db.scalars(select(Character).where(Character.id.in_(unique_ids))).all())
    if len(rows) != len(unique_ids):
        raise _invalid_reference("角色")
    by_id = {row.id: row for row in rows}
    return [by_id[row_id] for row_id in row_ids]


def _require_factions(db: Session, row_ids: Sequence[uuid.UUID]) -> list[Faction]:
    unique_ids = set(row_ids)
    rows = list(db.scalars(select(Faction).where(Faction.id.in_(unique_ids))).all())
    if len(rows) != len(unique_ids):
        raise _invalid_reference("势力")
    by_id = {row.id: row for row in rows}
    return [by_id[row_id] for row_id in row_ids]


def _require_events(db: Session, row_ids: Sequence[uuid.UUID]) -> list[StoryEvent]:
    unique_ids = set(row_ids)
    rows = list(db.scalars(select(StoryEvent).where(StoryEvent.id.in_(unique_ids))).all())
    if len(rows) != len(unique_ids):
        raise _invalid_reference("事件")
    by_id = {row.id: row for row in rows}
    return [by_id[row_id] for row_id in row_ids]


def _chapter_read(row: Chapter) -> AdminChapterRead:
    return AdminChapterRead.model_validate(row, from_attributes=True)


def _faction_read(row: Faction) -> AdminFactionRead:
    return AdminFactionRead.model_validate(row, from_attributes=True)


def _character_read(row: Character) -> AdminCharacterRead:
    return AdminCharacterRead.model_validate(row, from_attributes=True)


def _event_read(row: StoryEvent) -> AdminEventRead:
    return AdminEventRead(
        id=row.id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        impact=row.impact,
        chapter_id=row.chapter_id,
        sort_order=row.sort_order,
        spoiler_level=row.spoiler_level,
        visible_after_chapter_id=row.visible_after_chapter_id,
        status=row.status,
        character_ids=[character.id for character in row.characters],
        faction_ids=[faction.id for faction in row.factions],
    )


def _relationship_read(row: Relationship) -> AdminRelationshipRead:
    return AdminRelationshipRead(
        id=row.id,
        source_character_id=row.source_character_id,
        target_character_id=row.target_character_id,
        relation_type=row.relation_type,
        label=row.label,
        summary=row.summary,
        stage=row.stage,
        is_directional=row.is_directional,
        chapter_id=row.chapter_id,
        visible_after_chapter_id=row.visible_after_chapter_id,
        spoiler_level=row.spoiler_level,
        confidence=float(row.confidence),
        status=row.status,
        event_ids=[event.id for event in row.events],
    )


def get_bootstrap(db: Session) -> AdminContentBootstrap:
    chapters = list(db.scalars(select(Chapter).order_by(Chapter.sort_order)).all())
    factions = list(db.scalars(select(Faction).order_by(Faction.name)).all())
    characters = list(db.scalars(select(Character).order_by(Character.name)).all())
    events = list(
        db.scalars(
            select(StoryEvent)
            .options(
                selectinload(StoryEvent.characters),
                selectinload(StoryEvent.factions),
            )
            .order_by(StoryEvent.chapter_id, StoryEvent.sort_order)
        )
        .unique()
        .all()
    )
    relationships = list(
        db.scalars(
            select(Relationship)
            .options(selectinload(Relationship.events))
            .order_by(Relationship.created_at, Relationship.id)
        )
        .unique()
        .all()
    )
    return AdminContentBootstrap(
        chapters=[_chapter_read(row) for row in chapters],
        factions=[_faction_read(row) for row in factions],
        characters=[_character_read(row) for row in characters],
        events=[_event_read(row) for row in events],
        relationships=[_relationship_read(row) for row in relationships],
    )


def create_chapter(db: Session, body: AdminChapterWrite) -> AdminChapterRead:
    row = Chapter(**body.model_dump())
    db.add(row)
    _commit(db)
    db.refresh(row)
    return _chapter_read(row)


def update_chapter(db: Session, row_id: uuid.UUID, body: AdminChapterWrite) -> AdminChapterRead:
    row = db.scalar(select(Chapter).where(Chapter.id == row_id).with_for_update())
    if row is None:
        raise _not_found("章节")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    _commit(db)
    db.refresh(row)
    return _chapter_read(row)


def create_faction(db: Session, body: AdminFactionWrite) -> AdminFactionRead:
    _require_chapter(db, body.visible_after_chapter_id)
    row = Faction(**body.model_dump())
    db.add(row)
    _commit(db)
    db.refresh(row)
    return _faction_read(row)


def update_faction(db: Session, row_id: uuid.UUID, body: AdminFactionWrite) -> AdminFactionRead:
    row = db.scalar(select(Faction).where(Faction.id == row_id).with_for_update())
    if row is None:
        raise _not_found("势力")
    _require_chapter(db, body.visible_after_chapter_id)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    _commit(db)
    db.refresh(row)
    return _faction_read(row)


def create_character(db: Session, body: AdminCharacterWrite) -> AdminCharacterRead:
    _require_faction(db, body.faction_id)
    _require_chapter(db, body.first_appear_chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    row = Character(**body.model_dump())
    db.add(row)
    _commit(db)
    db.refresh(row)
    return _character_read(row)


def update_character(
    db: Session, row_id: uuid.UUID, body: AdminCharacterWrite
) -> AdminCharacterRead:
    row = db.scalar(select(Character).where(Character.id == row_id).with_for_update())
    if row is None:
        raise _not_found("角色")
    _require_faction(db, body.faction_id)
    _require_chapter(db, body.first_appear_chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    _commit(db)
    db.refresh(row)
    return _character_read(row)


def create_event(db: Session, body: AdminEventWrite) -> AdminEventRead:
    _require_chapter(db, body.chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    values = body.model_dump(exclude={"character_ids", "faction_ids"})
    row = StoryEvent(
        **values,
        characters=_require_characters(db, body.character_ids),
        factions=_require_factions(db, body.faction_ids),
    )
    db.add(row)
    _commit(db)
    db.refresh(row)
    return _event_read(row)


def update_event(db: Session, row_id: uuid.UUID, body: AdminEventWrite) -> AdminEventRead:
    row = db.scalar(
        select(StoryEvent)
        .options(
            selectinload(StoryEvent.characters),
            selectinload(StoryEvent.factions),
        )
        .where(StoryEvent.id == row_id)
        .with_for_update()
    )
    if row is None:
        raise _not_found("事件")
    _require_chapter(db, body.chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    for key, value in body.model_dump(exclude={"character_ids", "faction_ids"}).items():
        setattr(row, key, value)
    row.characters = _require_characters(db, body.character_ids)
    row.factions = _require_factions(db, body.faction_ids)
    _commit(db)
    db.refresh(row)
    return _event_read(row)


def create_relationship(db: Session, body: AdminRelationshipWrite) -> AdminRelationshipRead:
    characters = _require_characters(db, [body.source_character_id, body.target_character_id])
    _require_chapter(db, body.chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    values = body.model_dump(exclude={"event_ids", "source_character_id", "target_character_id"})
    row = Relationship(
        **values,
        source_character_id=characters[0].id,
        target_character_id=characters[1].id,
        events=_require_events(db, body.event_ids),
    )
    db.add(row)
    _commit(db)
    db.refresh(row)
    return _relationship_read(row)


def update_relationship(
    db: Session, row_id: uuid.UUID, body: AdminRelationshipWrite
) -> AdminRelationshipRead:
    row = db.scalar(
        select(Relationship)
        .options(selectinload(Relationship.events))
        .where(Relationship.id == row_id)
        .with_for_update()
    )
    if row is None:
        raise _not_found("关系")
    _require_characters(db, [body.source_character_id, body.target_character_id])
    _require_chapter(db, body.chapter_id)
    _require_chapter(db, body.visible_after_chapter_id)
    for key, value in body.model_dump(exclude={"event_ids"}).items():
        setattr(row, key, value)
    row.events = _require_events(db, body.event_ids)
    _commit(db)
    db.refresh(row)
    return _relationship_read(row)


def archive_content(
    db: Session,
    resource: str,
    row_id: uuid.UUID,
) -> ArchiveResult:
    row: Chapter | Faction | Character | StoryEvent | Relationship | None
    if resource == "chapters":
        row = db.scalar(select(Chapter).where(Chapter.id == row_id).with_for_update())
    elif resource == "factions":
        row = db.scalar(select(Faction).where(Faction.id == row_id).with_for_update())
    elif resource == "characters":
        row = db.scalar(select(Character).where(Character.id == row_id).with_for_update())
    elif resource == "events":
        row = db.scalar(select(StoryEvent).where(StoryEvent.id == row_id).with_for_update())
    elif resource == "relationships":
        row = db.scalar(select(Relationship).where(Relationship.id == row_id).with_for_update())
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理资源不存在。",
        )
    if row is None:
        raise _not_found("内容")
    row.status = ContentStatus.ARCHIVED
    _commit(db)
    return ArchiveResult(id=row.id, status=row.status)
