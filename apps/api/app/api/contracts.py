import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import (
    ProgressKey,
    RelationType,
    SubmissionStatus,
    SubmissionType,
)


class AdminLogin(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=512)


class SessionData(BaseModel):
    username: str
    csrf_token: str
    expires_in_minutes: int


class SubmissionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=10, max_length=4000)
    source_character_slug: str | None = Field(default=None, max_length=100)
    target_character_slug: str | None = Field(default=None, max_length=100)
    character_slug: str | None = Field(default=None, max_length=100)
    chapter_slug: str | None = Field(default=None, max_length=80)
    relation_type: RelationType | None = None
    spoiler_level: int = Field(default=0, ge=0, le=3)


class PublicSubmissionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    submission_type: SubmissionType
    payload: SubmissionPayload
    source_note: str = Field(min_length=10, max_length=4000)
    contact: str | None = Field(default=None, max_length=200)
    website: str = Field(default="", max_length=0)

    @field_validator("contact")
    @classmethod
    def normalize_contact(cls, value: str | None) -> str | None:
        return value or None


class SubmissionPublicReceipt(BaseModel):
    id: uuid.UUID
    status: SubmissionStatus
    message: str


class SubmissionAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_type: SubmissionType
    payload: dict[str, object]
    source_note: str
    contact: str | None
    status: SubmissionStatus
    review_note: str | None
    created_at: datetime


class ReviewSubmission(BaseModel):
    action: Literal["approve", "reject"]
    review_note: str = Field(min_length=2, max_length=2000)


class TimelineCharacter(BaseModel):
    slug: str
    name: str


class TimelineEvent(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    impact: str | None
    chapter_slug: str
    chapter_title: str
    sort_order: int
    characters: list[TimelineCharacter]


class TimelineData(BaseModel):
    progress: ProgressKey
    events: list[TimelineEvent]


class CharacterDetail(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    summary: str
    interpretation: str | None
    identity_tags: list[str]
    faction_name: str | None
    first_appear_chapter: str | None


class RelationshipDetail(BaseModel):
    id: uuid.UUID
    source_name: str
    target_name: str
    relation_type: RelationType
    label: str
    summary: str
    stage: str | None
    confidence: float


class SearchResult(BaseModel):
    kind: Literal["character", "faction", "event"]
    slug: str
    title: str
    summary: str
    score: float


class SearchData(BaseModel):
    query: str
    results: list[SearchResult]


class PathNode(BaseModel):
    id: uuid.UUID
    slug: str
    name: str


class PathEdge(BaseModel):
    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    label: str
    relation_type: RelationType


class RelationshipPathData(BaseModel):
    found: bool
    nodes: list[PathNode]
    edges: list[PathEdge]


class AIExtractionRequest(BaseModel):
    note: str = Field(min_length=20, max_length=20000)


class AIRelationshipCandidate(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    relation_type: RelationType
    summary: str = Field(min_length=5, max_length=1000)
    spoiler_level: int = Field(ge=0, le=3)
    chapter_slug: str | None = Field(default=None, max_length=80)
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class AIEventCandidate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=5, max_length=2000)
    character_names: list[str] = Field(default_factory=list, max_length=30)
    chapter_slug: str | None = Field(default=None, max_length=80)
    spoiler_level: int = Field(ge=0, le=3)
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class AIExtractionResult(BaseModel):
    run_id: uuid.UUID | None = None
    characters: list[str] = Field(default_factory=list, max_length=100)
    relationships: list[AIRelationshipCandidate] = Field(default_factory=list, max_length=100)
    events: list[AIEventCandidate] = Field(default_factory=list, max_length=100)
    model: str
    prompt_version: str
