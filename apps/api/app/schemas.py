import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain import (
    ProgressKey,
    RelationType,
    SourceType,
    SubmissionStatus,
    SubmissionType,
)

# ── envelope ──────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, list[str]] | None = None


class ResponseMeta(BaseModel):
    request_id: str | None = None
    next_cursor: str | None = None


class ApiResponse[T](BaseModel):
    data: T | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


# ── health / system ───────────────────────────────────────────────────


class HealthData(BaseModel):
    status: str
    environment: str


class RestrictedData(BaseModel):
    restricted: bool = True
    required_progress: ProgressKey | None = None
    message: str = "该内容涉及后续剧情，已隐藏。"


# ── graph ─────────────────────────────────────────────────────────────


class GraphNode(BaseModel):
    id: uuid.UUID
    slug: str
    label: str
    faction_id: uuid.UUID | None
    faction_name: str | None
    importance: int
    summary: str


class GraphEdge(BaseModel):
    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    relation_type: RelationType
    label: str
    summary: str
    directional: bool
    confidence: float = Field(ge=0, le=1)


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    progress: ProgressKey


# ── submission ────────────────────────────────────────────────────────


class SubmissionCreate(BaseModel):
    submission_type: SubmissionType
    payload: dict[str, str | int | bool | list[str]]
    source_note: str = Field(min_length=10, max_length=4000)
    contact: str | None = Field(default=None, max_length=200)
    website: str = Field(default="", max_length=0, exclude=True)


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_type: SubmissionType
    payload: dict[str, object]
    source_note: str
    contact: str | None
    status: SubmissionStatus
    review_note: str | None
    created_at: datetime


# ── chapter ───────────────────────────────────────────────────────────


class ChapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    region: str | None
    sort_order: int
    progress_key: ProgressKey
    progress_rank: int
    created_at: datetime
    updated_at: datetime


# ── faction ───────────────────────────────────────────────────────────


class FactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    faction_type: str
    summary: str
    spoiler_level: int
    visible_after_chapter_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ── character ─────────────────────────────────────────────────────────


class CharacterAliasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alias: str


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    summary: str
    interpretation: str | None
    identity_tags: list[str]
    faction_id: uuid.UUID | None
    importance: int
    spoiler_level: int
    first_appear_chapter_id: uuid.UUID | None
    visible_after_chapter_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    aliases: list[CharacterAliasRead] = Field(default_factory=list)


class CharacterListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    summary: str
    identity_tags: list[str]
    faction_id: uuid.UUID | None
    importance: int
    spoiler_level: int
    first_appear_chapter_id: uuid.UUID | None
    visible_after_chapter_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ── story event ───────────────────────────────────────────────────────


class StoryEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    summary: str
    impact: str | None
    chapter_id: uuid.UUID
    sort_order: int
    spoiler_level: int
    visible_after_chapter_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ── source ────────────────────────────────────────────────────────────


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: SourceType
    title: str
    reference: str | None
    note: str | None
    chapter_id: uuid.UUID | None
    faction_id: uuid.UUID | None
    character_id: uuid.UUID | None
    event_id: uuid.UUID | None
    relationship_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
