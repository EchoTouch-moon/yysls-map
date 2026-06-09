"""Import a normalized content dataset into the application database."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.domain import ContentStatus, ProgressKey, RelationType, SourceType
from app.models import (
    Chapter,
    Character,
    CharacterAlias,
    Faction,
    Relationship,
    Source,
    StoryEvent,
)

CONTENT_NAMESPACE = uuid.UUID("53d19073-c46e-47d4-b688-b2d4b6f47e31")


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetMeta(ImportModel):
    id: str
    title: str
    game: str
    language: str
    collected_at: str
    content_scope: str
    disclaimer: str


class ChapterItem(ImportModel):
    id: str
    slug: str
    title: str
    region: str | None
    sort_order: int = Field(ge=0)
    progress_key: ProgressKey
    progress_rank: int = Field(ge=0, le=100)
    summary: str
    source_ids: list[str]


class FactionItem(ImportModel):
    id: str
    slug: str
    name: str
    faction_type: str
    summary: str
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey
    source_ids: list[str]


class CharacterItem(ImportModel):
    id: str
    slug: str
    name: str
    aliases: list[str]
    summary: str
    interpretation: str | None
    identity_tags: list[str]
    faction_id: str | None
    importance: int = Field(ge=1, le=5)
    spoiler_level: int = Field(ge=0, le=3)
    first_appear_chapter_id: str
    visible_after_progress: ProgressKey
    source_ids: list[str]
    review_note: str | None = None


class EventItem(ImportModel):
    id: str
    slug: str
    title: str
    summary: str
    impact: str | None
    chapter_id: str
    part: int = Field(ge=0)
    sort_order: int = Field(ge=0)
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey
    character_ids: list[str]
    faction_ids: list[str]
    source_ids: list[str]


class RelationshipItem(ImportModel):
    id: str
    source_character_id: str
    target_character_id: str
    relation_type: RelationType
    label: str
    summary: str
    stage: str | None
    directional: bool
    chapter_id: str
    event_ids: list[str]
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey
    confidence: float = Field(ge=0, le=1)
    source_ids: list[str]
    review_note: str | None = None


class SourceItem(ImportModel):
    id: str
    source_type: SourceType
    title: str
    reference: str
    locator: str
    accessed_at: str
    note: str | None


class ContentDataset(ImportModel):
    schema_version: str
    dataset: DatasetMeta
    chapters: list[ChapterItem]
    factions: list[FactionItem]
    characters: list[CharacterItem]
    events: list[EventItem]
    relationships: list[RelationshipItem]
    sources: list[SourceItem]


class ImportStats(BaseModel):
    chapters: int
    factions: int
    characters: int
    events: int
    relationships: int
    source_definitions: int
    source_links: int


def stable_content_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(CONTENT_NAMESPACE, f"{kind}:{key}")


def load_dataset(path: Path) -> ContentDataset:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return ContentDataset.model_validate(payload)


def _clear_content(db: Session) -> None:
    for model in (
        Source,
        Relationship,
        StoryEvent,
        CharacterAlias,
        Character,
        Faction,
        Chapter,
    ):
        db.execute(delete(model))
    db.flush()


def _progress_gate(
    db: Session,
    progress: ProgressKey,
    chapters_by_progress: dict[ProgressKey, Chapter],
) -> uuid.UUID | None:
    if progress is ProgressKey.UNRESTRICTED:
        return None
    if chapter := chapters_by_progress.get(progress):
        return chapter.id

    progress_ranks = {
        ProgressKey.START: 0,
        ProgressKey.QINGHE: 10,
        ProgressKey.KAIFENG: 20,
        ProgressKey.CURRENT: 90,
    }
    gate_id = stable_content_id("progress-gate", progress.value)
    gate = db.get(Chapter, gate_id)
    if gate is None:
        gate = Chapter(
            id=gate_id,
            slug=f"internal-gate-{progress.value}",
            title=f"内部进度门槛：{progress.value}",
            region=None,
            sort_order=1000 + progress_ranks[progress],
            progress_key=progress,
            progress_rank=progress_ranks[progress],
            status=ContentStatus.ARCHIVED,
        )
        db.add(gate)
        db.flush()
    chapters_by_progress[progress] = gate
    return gate.id


def _source_note(source: SourceItem) -> str:
    parts = [f"定位：{source.locator}", f"访问日期：{source.accessed_at}"]
    if source.note:
        parts.append(source.note)
    return "\n".join(parts)


def _add_subject_sources(
    db: Session,
    *,
    source_definitions: dict[str, SourceItem],
    kind: str,
    item_id: str,
    source_ids: list[str],
) -> int:
    subject_id = stable_content_id(kind, item_id)
    for source_id in source_ids:
        definition = source_definitions[source_id]
        db.add(
            Source(
                id=stable_content_id("source-link", f"{source_id}:{kind}:{item_id}"),
                source_type=definition.source_type,
                title=definition.title,
                reference=definition.reference,
                note=_source_note(definition),
                character_id=subject_id if kind == "character" else None,
                event_id=subject_id if kind == "event" else None,
                relationship_id=subject_id if kind == "relationship" else None,
            )
        )
    return len(source_ids)


def import_dataset(
    db: Session,
    dataset: ContentDataset,
    *,
    replace_existing: bool = False,
) -> ImportStats:
    if replace_existing:
        _clear_content(db)

    source_definitions = {item.id: item for item in dataset.sources}

    chapters: dict[str, Chapter] = {}
    chapters_by_progress: dict[ProgressKey, Chapter] = {}
    for chapter_item in dataset.chapters:
        row_id = stable_content_id("chapter", chapter_item.id)
        chapter = db.get(Chapter, row_id)
        if chapter is None:
            chapter = Chapter(id=row_id)
            db.add(chapter)
        chapter.slug = chapter_item.slug
        chapter.title = chapter_item.title
        chapter.region = chapter_item.region
        chapter.sort_order = chapter_item.sort_order
        chapter.progress_key = chapter_item.progress_key
        chapter.progress_rank = chapter_item.progress_rank
        chapter.status = ContentStatus.PUBLISHED
        chapters[chapter_item.id] = chapter
        chapters_by_progress[chapter_item.progress_key] = chapter
    db.flush()

    factions: dict[str, Faction] = {}
    for faction_item in dataset.factions:
        row_id = stable_content_id("faction", faction_item.id)
        faction = db.get(Faction, row_id)
        if faction is None:
            faction = Faction(id=row_id)
            db.add(faction)
        faction.slug = faction_item.slug
        faction.name = faction_item.name
        faction.faction_type = faction_item.faction_type
        faction.summary = faction_item.summary
        faction.spoiler_level = faction_item.spoiler_level
        faction.visible_after_chapter_id = _progress_gate(
            db, faction_item.visible_after_progress, chapters_by_progress
        )
        faction.status = ContentStatus.PUBLISHED
        factions[faction_item.id] = faction
    db.flush()

    characters: dict[str, Character] = {}
    for character_item in dataset.characters:
        row_id = stable_content_id("character", character_item.id)
        character = db.get(Character, row_id)
        if character is None:
            character = Character(id=row_id)
            db.add(character)
        character.slug = character_item.slug
        character.name = character_item.name
        character.summary = character_item.summary
        character.interpretation = character_item.interpretation
        character.identity_tags = character_item.identity_tags
        character.faction_id = (
            factions[character_item.faction_id].id
            if character_item.faction_id
            else None
        )
        character.importance = character_item.importance
        character.spoiler_level = character_item.spoiler_level
        character.first_appear_chapter_id = chapters[
            character_item.first_appear_chapter_id
        ].id
        character.visible_after_chapter_id = _progress_gate(
            db, character_item.visible_after_progress, chapters_by_progress
        )
        character.status = ContentStatus.PUBLISHED
        character.aliases.clear()
        character.aliases.extend(
            CharacterAlias(
                id=stable_content_id("alias", f"{character_item.id}:{alias}"),
                alias=alias,
            )
            for alias in character_item.aliases
        )
        characters[character_item.id] = character
    db.flush()

    events: dict[str, StoryEvent] = {}
    for event_item in dataset.events:
        row_id = stable_content_id("event", event_item.id)
        event = db.get(StoryEvent, row_id)
        if event is None:
            event = StoryEvent(id=row_id)
            db.add(event)
        event.slug = event_item.slug
        event.title = event_item.title
        event.summary = event_item.summary
        event.impact = event_item.impact
        event.chapter_id = chapters[event_item.chapter_id].id
        event.sort_order = event_item.sort_order
        event.spoiler_level = event_item.spoiler_level
        event.visible_after_chapter_id = _progress_gate(
            db, event_item.visible_after_progress, chapters_by_progress
        )
        event.status = ContentStatus.PUBLISHED
        event.characters = [
            characters[character_id] for character_id in event_item.character_ids
        ]
        event.factions = [
            factions[faction_id] for faction_id in event_item.faction_ids
        ]
        events[event_item.id] = event
    db.flush()

    relationships: dict[str, Relationship] = {}
    for relationship_item in dataset.relationships:
        row_id = stable_content_id("relationship", relationship_item.id)
        relationship = db.get(Relationship, row_id)
        if relationship is None:
            relationship = Relationship(id=row_id)
            db.add(relationship)
        relationship.source_character_id = characters[
            relationship_item.source_character_id
        ].id
        relationship.target_character_id = characters[
            relationship_item.target_character_id
        ].id
        relationship.relation_type = relationship_item.relation_type
        relationship.label = relationship_item.label
        relationship.summary = relationship_item.summary
        relationship.stage = relationship_item.stage
        relationship.is_directional = relationship_item.directional
        relationship.chapter_id = chapters[relationship_item.chapter_id].id
        relationship.visible_after_chapter_id = _progress_gate(
            db, relationship_item.visible_after_progress, chapters_by_progress
        )
        relationship.spoiler_level = relationship_item.spoiler_level
        relationship.confidence = relationship_item.confidence
        relationship.status = ContentStatus.PUBLISHED
        relationship.events = [
            events[event_id] for event_id in relationship_item.event_ids
        ]
        relationships[relationship_item.id] = relationship
    db.flush()

    imported_subject_ids = [
        *(character.id for character in characters.values()),
        *(event.id for event in events.values()),
        *(relationship.id for relationship in relationships.values()),
    ]
    if imported_subject_ids:
        db.execute(
            delete(Source).where(
                (Source.character_id.in_(imported_subject_ids))
                | (Source.event_id.in_(imported_subject_ids))
                | (Source.relationship_id.in_(imported_subject_ids))
            )
        )

    source_links = 0
    for character_item in dataset.characters:
        source_links += _add_subject_sources(
            db,
            source_definitions=source_definitions,
            kind="character",
            item_id=character_item.id,
            source_ids=character_item.source_ids,
        )
    for event_item in dataset.events:
        source_links += _add_subject_sources(
            db,
            source_definitions=source_definitions,
            kind="event",
            item_id=event_item.id,
            source_ids=event_item.source_ids,
        )
    for relationship_item in dataset.relationships:
        source_links += _add_subject_sources(
            db,
            source_definitions=source_definitions,
            kind="relationship",
            item_id=relationship_item.id,
            source_ids=relationship_item.source_ids,
        )
    db.flush()

    return ImportStats(
        chapters=len(dataset.chapters),
        factions=len(dataset.factions),
        characters=len(dataset.characters),
        events=len(dataset.events),
        relationships=len(dataset.relationships),
        source_definitions=len(dataset.sources),
        source_links=source_links,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing graph content before importing this dataset.",
    )
    args = parser.parse_args()
    dataset = load_dataset(args.dataset)

    with SessionLocal() as db:
        try:
            stats = import_dataset(
                db,
                dataset,
                replace_existing=args.replace_existing,
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"Content import failed: {exc}", file=sys.stderr)
            raise
    print(f"Content import ready: {stats.model_dump_json()}")


if __name__ == "__main__":
    main()
