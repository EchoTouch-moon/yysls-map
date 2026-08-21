"""Pydantic contracts for normalized content datasets."""

from __future__ import annotations

import uuid
from datetime import date
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import (
    HistoricalFactKind,
    HistoricalReferenceType,
    HistoricalRelationKind,
    ProgressKey,
    RelationType,
    SourceType,
    StoryBeatRole,
)

CONTENT_NAMESPACE = uuid.UUID("53d19073-c46e-47d4-b688-b2d4b6f47e31")


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

