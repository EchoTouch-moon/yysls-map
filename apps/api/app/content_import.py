"""Import a normalized content dataset into the application database."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from collections.abc import Callable, Hashable, Sequence
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.domain import (
    ContentStatus,
    HistoricalFactKind,
    HistoricalReferenceType,
    HistoricalRelationKind,
    ProgressKey,
    RelationType,
    SourceType,
    StoryBeatRole,
)
from app.models import (
    Chapter,
    Character,
    CharacterAlias,
    ContentImportRun,
    EventHistoricalLink,
    Faction,
    HistoricalContext,
    HistoricalReference,
    Relationship,
    Source,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
)

CONTENT_NAMESPACE = uuid.UUID("53d19073-c46e-47d4-b688-b2d4b6f47e31")
CONTENT_IMPORT_LOCK_KEY = 5_664_314_909_166_029_169


class ContentValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetMeta(ImportModel):
    id: str
    title: str
    game: str
    language: str
    collected_at: date
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


class StoryArcBeatItem(ImportModel):
    id: str
    event_id: str
    sort_order: int = Field(ge=0)
    role: StoryBeatRole
    guide: str
    why_it_matters: str
    bridge: str
    next_question: str
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey


class StoryArcItem(ImportModel):
    id: str
    slug: str
    title: str
    summary: str
    core_question: str
    estimated_minutes: int = Field(ge=1, le=60)
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey
    beats: list[StoryArcBeatItem] = Field(min_length=1)


class HistoricalReferenceItem(ImportModel):
    id: str
    slug: str
    reference_type: HistoricalReferenceType
    title: str
    publisher: str
    url: str
    locator: str | None
    accessed_at: date

    @field_validator("url")
    @classmethod
    def validate_public_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.hostname is None:
            raise ValueError("historical reference URL must be an absolute http or https URL")
        return value


class HistoricalContextItem(ImportModel):
    id: str
    slug: str
    title: str
    period_label: str
    summary: str
    fact_kind: HistoricalFactKind
    boundary_note: str
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey
    reference_ids: list[str] = Field(min_length=1)


class EventHistoricalLinkItem(ImportModel):
    id: str
    event_id: str
    historical_context_id: str
    relation_kind: HistoricalRelationKind
    editorial_note: str
    sort_order: int = Field(ge=0)
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_progress: ProgressKey


class ContentDataset(ImportModel):
    schema_version: str
    dataset: DatasetMeta
    chapters: list[ChapterItem]
    factions: list[FactionItem]
    characters: list[CharacterItem]
    events: list[EventItem]
    relationships: list[RelationshipItem]
    sources: list[SourceItem]
    story_arcs: list[StoryArcItem]
    historical_references: list[HistoricalReferenceItem]
    historical_contexts: list[HistoricalContextItem]
    event_historical_links: list[EventHistoricalLinkItem]


class ImportStats(BaseModel):
    chapters: int
    factions: int
    characters: int
    events: int
    relationships: int
    source_definitions: int
    source_links: int
    story_arcs: int
    story_arc_beats: int
    historical_references: int
    historical_contexts: int
    event_historical_links: int


def stable_content_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(CONTENT_NAMESPACE, f"{kind}:{key}")


def load_dataset(path: Path) -> ContentDataset:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    dataset = ContentDataset.model_validate(payload)
    validate_dataset(dataset)
    return dataset


def _duplicates[HashableT: Hashable](
    values: Sequence[HashableT],
) -> set[HashableT]:
    seen: set[HashableT] = set()
    duplicates: set[HashableT] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _duplicate_integers(values: Sequence[int]) -> set[int]:
    return {value for value in values if values.count(value) > 1}


def _duplicate_string_pairs(
    values: Sequence[tuple[str, str]],
) -> set[tuple[str, str]]:
    return {value for value in values if values.count(value) > 1}


def _duplicate_event_orders(
    values: Sequence[tuple[str, int]],
) -> set[tuple[str, int]]:
    return {value for value in values if values.count(value) > 1}


def _check_references(
    errors: list[str],
    *,
    label: str,
    references: Sequence[str],
    available: set[str],
) -> None:
    missing = sorted(set(references) - available)
    if missing:
        errors.append(f"{label} references missing IDs: {', '.join(missing)}")


def validate_dataset(dataset: ContentDataset) -> None:
    errors: list[str] = []
    if dataset.schema_version != "1.1":
        errors.append(f"unsupported schema version: {dataset.schema_version}")
    if dataset.dataset.game != "燕云十六声":
        errors.append(f"unexpected game: {dataset.dataset.game}")
    if dataset.dataset.language != "zh-CN":
        errors.append(f"unexpected language: {dataset.dataset.language}")
    id_collections: list[tuple[str, Sequence[str]]] = [
        ("chapter", [item.id for item in dataset.chapters]),
        ("faction", [item.id for item in dataset.factions]),
        ("character", [item.id for item in dataset.characters]),
        ("event", [item.id for item in dataset.events]),
        ("relationship", [item.id for item in dataset.relationships]),
        ("source", [item.id for item in dataset.sources]),
        ("story arc", [item.id for item in dataset.story_arcs]),
        (
            "story arc beat",
            [beat.id for arc in dataset.story_arcs for beat in arc.beats],
        ),
        (
            "historical reference",
            [item.id for item in dataset.historical_references],
        ),
        ("historical context", [item.id for item in dataset.historical_contexts]),
        ("event historical link", [item.id for item in dataset.event_historical_links]),
    ]
    for label, item_ids in id_collections:
        duplicate_ids = sorted(_duplicates(item_ids))
        if duplicate_ids:
            errors.append(f"duplicate {label} IDs: {', '.join(duplicate_ids)}")

    slug_collections: list[tuple[str, Sequence[str]]] = [
        ("chapter", [item.slug for item in dataset.chapters]),
        ("faction", [item.slug for item in dataset.factions]),
        ("character", [item.slug for item in dataset.characters]),
        ("event", [item.slug for item in dataset.events]),
        ("story arc", [item.slug for item in dataset.story_arcs]),
        (
            "historical reference",
            [item.slug for item in dataset.historical_references],
        ),
        ("historical context", [item.slug for item in dataset.historical_contexts]),
    ]
    for label, slugs in slug_collections:
        duplicate_slugs = sorted(_duplicates(slugs))
        if duplicate_slugs:
            errors.append(f"duplicate {label} slugs: {', '.join(duplicate_slugs)}")

    duplicate_chapter_orders = sorted(_duplicates([item.sort_order for item in dataset.chapters]))
    if duplicate_chapter_orders:
        errors.append(
            "duplicate chapter sort orders: "
            + ", ".join(str(value) for value in duplicate_chapter_orders)
        )
    duplicate_progress = sorted(_duplicates([item.progress_key.value for item in dataset.chapters]))
    if duplicate_progress:
        errors.append(f"duplicate progress gates: {', '.join(duplicate_progress)}")

    event_orders = [(item.chapter_id, item.sort_order) for item in dataset.events]
    duplicate_event_orders = sorted(_duplicates(event_orders))
    if duplicate_event_orders:
        errors.append(
            "duplicate event sort orders: "
            + ", ".join(f"{chapter}:{order}" for chapter, order in duplicate_event_orders)
        )

    for character in dataset.characters:
        duplicate_aliases = sorted(_duplicates(character.aliases))
        if duplicate_aliases:
            errors.append(
                f"duplicate aliases for character {character.id}: " + ", ".join(duplicate_aliases)
            )

    relationship_identities = [
        (
            item.source_character_id,
            item.target_character_id,
            item.relation_type.value,
            item.chapter_id,
        )
        for item in dataset.relationships
    ]
    if duplicate_relationships := sorted(_duplicates(relationship_identities)):
        errors.append(
            "duplicate relationship identities: "
            + ", ".join(":".join(identity) for identity in duplicate_relationships)
        )

    chapter_ids = {item.id for item in dataset.chapters}
    faction_ids = {item.id for item in dataset.factions}
    character_ids = {item.id for item in dataset.characters}
    event_ids = {item.id for item in dataset.events}
    source_ids = {item.id for item in dataset.sources}
    historical_reference_ids = {item.id for item in dataset.historical_references}
    historical_context_ids = {item.id for item in dataset.historical_contexts}

    for chapter in dataset.chapters:
        if duplicates := sorted(_duplicates(chapter.source_ids)):
            errors.append(f"duplicate sources for chapter {chapter.id}: " + ", ".join(duplicates))
        _check_references(
            errors,
            label=f"chapter {chapter.id} sources",
            references=chapter.source_ids,
            available=source_ids,
        )
    for faction in dataset.factions:
        if duplicates := sorted(_duplicates(faction.source_ids)):
            errors.append(f"duplicate sources for faction {faction.id}: " + ", ".join(duplicates))
        _check_references(
            errors,
            label=f"faction {faction.id} sources",
            references=faction.source_ids,
            available=source_ids,
        )
    for character in dataset.characters:
        if character.faction_id and character.faction_id not in faction_ids:
            errors.append(
                f"character {character.id} references missing faction: {character.faction_id}"
            )
        if character.first_appear_chapter_id not in chapter_ids:
            errors.append(
                f"character {character.id} references missing chapter: "
                f"{character.first_appear_chapter_id}"
            )
        if duplicates := sorted(_duplicates(character.source_ids)):
            errors.append(
                f"duplicate sources for character {character.id}: " + ", ".join(duplicates)
            )
        _check_references(
            errors,
            label=f"character {character.id} sources",
            references=character.source_ids,
            available=source_ids,
        )
    for event in dataset.events:
        if event.chapter_id not in chapter_ids:
            errors.append(f"event {event.id} references missing chapter: {event.chapter_id}")
        for label, references in (
            ("characters", event.character_ids),
            ("factions", event.faction_ids),
            ("sources", event.source_ids),
        ):
            if duplicates := sorted(_duplicates(references)):
                errors.append(f"duplicate {label} for event {event.id}: " + ", ".join(duplicates))
        _check_references(
            errors,
            label=f"event {event.id} characters",
            references=event.character_ids,
            available=character_ids,
        )
        _check_references(
            errors,
            label=f"event {event.id} factions",
            references=event.faction_ids,
            available=faction_ids,
        )
        _check_references(
            errors,
            label=f"event {event.id} sources",
            references=event.source_ids,
            available=source_ids,
        )
    for relationship in dataset.relationships:
        if relationship.source_character_id == relationship.target_character_id:
            errors.append(f"relationship {relationship.id} references itself")
        _check_references(
            errors,
            label=f"relationship {relationship.id} characters",
            references=[
                relationship.source_character_id,
                relationship.target_character_id,
            ],
            available=character_ids,
        )
        if relationship.chapter_id not in chapter_ids:
            errors.append(
                f"relationship {relationship.id} references missing chapter: "
                f"{relationship.chapter_id}"
            )
        for label, references in (
            ("events", relationship.event_ids),
            ("sources", relationship.source_ids),
        ):
            if duplicates := sorted(_duplicates(references)):
                errors.append(
                    f"duplicate {label} for relationship {relationship.id}: "
                    + ", ".join(duplicates)
                )
        _check_references(
            errors,
            label=f"relationship {relationship.id} events",
            references=relationship.event_ids,
            available=event_ids,
        )
        _check_references(
            errors,
            label=f"relationship {relationship.id} sources",
            references=relationship.source_ids,
            available=source_ids,
        )

    for arc in dataset.story_arcs:
        beat_orders = [beat.sort_order for beat in arc.beats]
        if duplicate_beat_orders := _duplicate_integers(beat_orders):
            errors.append(
                f"duplicate beat sort orders for story arc {arc.id}: "
                + ", ".join(sorted(str(value) for value in duplicate_beat_orders))
            )
        beat_event_ids = [beat.event_id for beat in arc.beats]
        if duplicates := sorted(_duplicates(beat_event_ids)):
            errors.append(f"duplicate beat events for story arc {arc.id}: " + ", ".join(duplicates))
        _check_references(
            errors,
            label=f"story arc {arc.id} beat events",
            references=beat_event_ids,
            available=event_ids,
        )

    for context in dataset.historical_contexts:
        if duplicates := sorted(_duplicates(context.reference_ids)):
            errors.append(
                f"duplicate references for historical context {context.id}: "
                + ", ".join(duplicates)
            )
        _check_references(
            errors,
            label=f"historical context {context.id} references",
            references=context.reference_ids,
            available=historical_reference_ids,
        )

    link_identities = [
        (item.event_id, item.historical_context_id) for item in dataset.event_historical_links
    ]
    if duplicate_link_identities := _duplicate_string_pairs(link_identities):
        errors.append(
            "duplicate event historical links: "
            + ", ".join(
                sorted(f"{event}:{context}" for event, context in duplicate_link_identities)
            )
        )
    link_orders = [(item.event_id, item.sort_order) for item in dataset.event_historical_links]
    if duplicate_link_orders := _duplicate_event_orders(link_orders):
        errors.append(
            "duplicate event historical link sort orders: "
            + ", ".join(
                sorted(f"{event}:{sort_order}" for event, sort_order in duplicate_link_orders)
            )
        )
    for link in dataset.event_historical_links:
        _check_references(
            errors,
            label=f"event historical link {link.id} event",
            references=[link.event_id],
            available=event_ids,
        )
        _check_references(
            errors,
            label=f"event historical link {link.id} context",
            references=[link.historical_context_id],
            available=historical_context_ids,
        )

    if errors:
        raise ContentValidationError(errors)


def _clear_content(db: Session) -> None:
    for model in (
        EventHistoricalLink,
        HistoricalContext,
        HistoricalReference,
        StoryArcBeat,
        StoryArc,
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
                chapter_id=subject_id if kind == "chapter" else None,
                faction_id=subject_id if kind == "faction" else None,
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
            factions[character_item.faction_id].id if character_item.faction_id else None
        )
        character.importance = character_item.importance
        character.spoiler_level = character_item.spoiler_level
        character.first_appear_chapter_id = chapters[character_item.first_appear_chapter_id].id
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
        event.characters = [characters[character_id] for character_id in event_item.character_ids]
        event.factions = [factions[faction_id] for faction_id in event_item.faction_ids]
        events[event_item.id] = event
    db.flush()

    relationships: dict[str, Relationship] = {}
    for relationship_item in dataset.relationships:
        row_id = stable_content_id("relationship", relationship_item.id)
        relationship = db.get(Relationship, row_id)
        if relationship is None:
            relationship = Relationship(id=row_id)
            db.add(relationship)
        relationship.source_character_id = characters[relationship_item.source_character_id].id
        relationship.target_character_id = characters[relationship_item.target_character_id].id
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
        relationship.events = [events[event_id] for event_id in relationship_item.event_ids]
        relationships[relationship_item.id] = relationship
    db.flush()

    historical_references: dict[str, HistoricalReference] = {}
    for reference_item in dataset.historical_references:
        row_id = stable_content_id("historical-reference", reference_item.id)
        reference = db.get(HistoricalReference, row_id)
        if reference is None:
            reference = HistoricalReference(id=row_id)
            db.add(reference)
        reference.slug = reference_item.slug
        reference.reference_type = reference_item.reference_type
        reference.title = reference_item.title
        reference.publisher = reference_item.publisher
        reference.url = reference_item.url
        reference.locator = reference_item.locator
        reference.accessed_at = reference_item.accessed_at
        historical_references[reference_item.id] = reference
    db.flush()

    historical_contexts: dict[str, HistoricalContext] = {}
    for context_item in dataset.historical_contexts:
        row_id = stable_content_id("historical-context", context_item.id)
        context = db.get(HistoricalContext, row_id)
        if context is None:
            context = HistoricalContext(id=row_id)
            db.add(context)
        context.slug = context_item.slug
        context.title = context_item.title
        context.period_label = context_item.period_label
        context.summary = context_item.summary
        context.fact_kind = context_item.fact_kind
        context.boundary_note = context_item.boundary_note
        context.visible_after_chapter_id = _progress_gate(
            db, context_item.visible_after_progress, chapters_by_progress
        )
        context.spoiler_level = context_item.spoiler_level
        context.status = ContentStatus.PUBLISHED
        context.references = [
            historical_references[reference_id] for reference_id in context_item.reference_ids
        ]
        historical_contexts[context_item.id] = context
    db.flush()

    event_ids_for_history = [event.id for event in events.values()]
    if event_ids_for_history:
        db.execute(
            delete(EventHistoricalLink).where(
                EventHistoricalLink.event_id.in_(event_ids_for_history)
            )
        )
    for link_item in dataset.event_historical_links:
        db.add(
            EventHistoricalLink(
                id=stable_content_id("event-historical-link", link_item.id),
                event_id=events[link_item.event_id].id,
                context_id=historical_contexts[link_item.historical_context_id].id,
                relation_kind=link_item.relation_kind,
                editorial_note=link_item.editorial_note,
                sort_order=link_item.sort_order,
                visible_after_chapter_id=_progress_gate(
                    db, link_item.visible_after_progress, chapters_by_progress
                ),
                spoiler_level=link_item.spoiler_level,
                status=ContentStatus.PUBLISHED,
            )
        )
    db.flush()

    story_arcs: dict[str, StoryArc] = {}
    for arc_item in dataset.story_arcs:
        row_id = stable_content_id("story-arc", arc_item.id)
        arc = db.get(StoryArc, row_id)
        if arc is None:
            arc = StoryArc(id=row_id)
            db.add(arc)
        arc.slug = arc_item.slug
        arc.title = arc_item.title
        arc.summary = arc_item.summary
        arc.core_question = arc_item.core_question
        arc.estimated_minutes = arc_item.estimated_minutes
        arc.visible_after_chapter_id = _progress_gate(
            db, arc_item.visible_after_progress, chapters_by_progress
        )
        arc.spoiler_level = arc_item.spoiler_level
        arc.status = ContentStatus.PUBLISHED
        db.execute(delete(StoryArcBeat).where(StoryArcBeat.arc_id == arc.id))
        db.flush()
        for beat_item in arc_item.beats:
            db.add(
                StoryArcBeat(
                    id=stable_content_id("story-arc-beat", beat_item.id),
                    arc_id=arc.id,
                    event_id=events[beat_item.event_id].id,
                    sort_order=beat_item.sort_order,
                    role=beat_item.role,
                    guide=beat_item.guide,
                    why_it_matters=beat_item.why_it_matters,
                    bridge=beat_item.bridge,
                    next_question=beat_item.next_question,
                    visible_after_chapter_id=_progress_gate(
                        db, beat_item.visible_after_progress, chapters_by_progress
                    ),
                    spoiler_level=beat_item.spoiler_level,
                    status=ContentStatus.PUBLISHED,
                )
            )
        story_arcs[arc_item.id] = arc
    db.flush()

    source_subjects = (
        (Source.chapter_id, [item.id for item in chapters.values()]),
        (Source.faction_id, [item.id for item in factions.values()]),
        (Source.character_id, [item.id for item in characters.values()]),
        (Source.event_id, [item.id for item in events.values()]),
        (Source.relationship_id, [item.id for item in relationships.values()]),
    )
    predicates = [column.in_(subject_ids) for column, subject_ids in source_subjects if subject_ids]
    if predicates:
        db.execute(delete(Source).where(or_(*predicates)))

    source_links = 0
    for kind, items in (
        ("chapter", dataset.chapters),
        ("faction", dataset.factions),
        ("character", dataset.characters),
        ("event", dataset.events),
        ("relationship", dataset.relationships),
    ):
        for item in items:
            source_links += _add_subject_sources(
                db,
                source_definitions=source_definitions,
                kind=kind,
                item_id=item.id,
                source_ids=item.source_ids,
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
        story_arcs=len(story_arcs),
        story_arc_beats=sum(len(arc.beats) for arc in dataset.story_arcs),
        historical_references=len(historical_references),
        historical_contexts=len(historical_contexts),
        event_historical_links=len(dataset.event_historical_links),
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_import(
    db: Session,
    *,
    dataset: ContentDataset,
    dataset_path: Path,
    replace_existing: bool,
) -> ImportStats:
    db.execute(select(func.pg_advisory_xact_lock(CONTENT_IMPORT_LOCK_KEY)))
    stats = import_dataset(
        db,
        dataset,
        replace_existing=replace_existing,
    )
    db.add(
        ContentImportRun(
            dataset_id=dataset.dataset.id,
            dataset_title=dataset.dataset.title,
            schema_version=dataset.schema_version,
            collected_at=dataset.dataset.collected_at,
            file_sha256=file_sha256(dataset_path),
            replaced_existing=replace_existing,
            stats=stats.model_dump(),
        )
    )
    db.flush()
    return stats


def main(
    argv: Sequence[str] | None = None,
    *,
    session_factory: Callable[[], Session] = SessionLocal,
) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the dataset without connecting to the database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the database import and always roll it back.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing graph content before importing this dataset.",
    )
    parser.add_argument(
        "--confirm-replace",
        metavar="DATASET_ID",
        help="Required confirmation value when using --replace-existing.",
    )
    args = parser.parse_args(argv)
    dataset = load_dataset(args.dataset)
    if args.replace_existing and args.confirm_replace != dataset.dataset.id:
        parser.error(f"--replace-existing requires --confirm-replace {dataset.dataset.id}")
    if args.confirm_replace and not args.replace_existing:
        parser.error("--confirm-replace requires --replace-existing")
    if args.validate_only:
        print(f"Content dataset valid: {dataset.dataset.id}")
        return

    with session_factory() as db:
        try:
            stats = run_import(
                db,
                dataset=dataset,
                dataset_path=args.dataset,
                replace_existing=args.replace_existing,
            )
            if args.dry_run:
                db.rollback()
            else:
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"Content import failed: {exc}", file=sys.stderr)
            raise
    status = "rolled back" if args.dry_run else "committed"
    print(f"Content import {status}: {stats.model_dump_json()}")


if __name__ == "__main__":
    main()
