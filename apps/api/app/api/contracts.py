import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.domain import (
    ContentStatus,
    HistoricalFactKind,
    HistoricalReferenceType,
    HistoricalRelationKind,
    ProgressKey,
    RelationType,
    SourceType,
    StoryBeatRole,
    SubmissionStatus,
    SubmissionType,
)


class AdminChapterWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    sort_order: int = Field(ge=0)
    progress_key: ProgressKey
    progress_rank: int = Field(ge=0, le=100)
    status: ContentStatus = ContentStatus.DRAFT


class AdminFactionWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=120)
    faction_type: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=4000)
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_chapter_id: uuid.UUID | None = None
    status: ContentStatus = ContentStatus.DRAFT


class AdminCharacterWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=4000)
    interpretation: str | None = Field(default=None, max_length=4000)
    identity_tags: list[str] = Field(default_factory=list, max_length=30)
    faction_id: uuid.UUID | None = None
    importance: int = Field(ge=1, le=5)
    spoiler_level: int = Field(ge=0, le=3)
    first_appear_chapter_id: uuid.UUID | None = None
    visible_after_chapter_id: uuid.UUID | None = None
    status: ContentStatus = ContentStatus.DRAFT


class AdminEventWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=4000)
    impact: str | None = Field(default=None, max_length=4000)
    chapter_id: uuid.UUID
    sort_order: int = Field(ge=0)
    spoiler_level: int = Field(ge=0, le=3)
    visible_after_chapter_id: uuid.UUID | None = None
    status: ContentStatus = ContentStatus.DRAFT
    character_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    faction_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)


class AdminRelationshipWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_character_id: uuid.UUID
    target_character_id: uuid.UUID
    relation_type: RelationType
    label: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=4000)
    stage: str | None = Field(default=None, max_length=120)
    is_directional: bool = True
    chapter_id: uuid.UUID | None = None
    visible_after_chapter_id: uuid.UUID | None = None
    spoiler_level: int = Field(ge=0, le=3)
    confidence: float = Field(ge=0, le=1)
    status: ContentStatus = ContentStatus.DRAFT
    event_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)

    @field_validator("target_character_id")
    @classmethod
    def characters_must_differ(cls, value: uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        if value == info.data.get("source_character_id"):
            raise ValueError("关系起点和终点不能相同")
        return value


class AdminChapterRead(AdminChapterWrite):
    id: uuid.UUID


class AdminFactionRead(AdminFactionWrite):
    id: uuid.UUID


class AdminCharacterRead(AdminCharacterWrite):
    id: uuid.UUID


class AdminEventRead(AdminEventWrite):
    id: uuid.UUID


class AdminRelationshipRead(AdminRelationshipWrite):
    id: uuid.UUID


class AdminContentBootstrap(BaseModel):
    chapters: list[AdminChapterRead]
    factions: list[AdminFactionRead]
    characters: list[AdminCharacterRead]
    events: list[AdminEventRead]
    relationships: list[AdminRelationshipRead]


class ArchiveResult(BaseModel):
    id: uuid.UUID
    status: ContentStatus


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


class EvidenceSource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_type: SourceType
    title: str
    reference: str | None


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
    sources: list[EvidenceSource] = Field(default_factory=list)


class TimelineData(BaseModel):
    progress: ProgressKey
    events: list[TimelineEvent]


class StoryArcListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    core_question: str
    estimated_minutes: int = Field(ge=1)
    beat_count: int = Field(ge=0)


class StoryArcListData(BaseModel):
    progress: ProgressKey
    arcs: list[StoryArcListItem]


class HistoricalReferenceRead(BaseModel):
    reference_type: HistoricalReferenceType
    title: str
    publisher: str
    url: str
    locator: str | None


class HistoricalContextRead(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    period_label: str
    summary: str
    fact_kind: HistoricalFactKind
    boundary_note: str
    relation_kind: HistoricalRelationKind
    editorial_note: str
    references: list[HistoricalReferenceRead]


class StoryArcBeatEvent(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    impact: str | None
    chapter_slug: str
    chapter_title: str
    characters: list[TimelineCharacter]
    sources: list[EvidenceSource]


class StoryArcRelationship(BaseModel):
    id: uuid.UUID
    relation_type: RelationType
    label: str
    source_slug: str
    source_name: str
    target_slug: str
    target_name: str


class StoryArcBeatRead(BaseModel):
    id: uuid.UUID
    sort_order: int
    role: StoryBeatRole
    guide: str
    why_it_matters: str
    bridge: str
    next_question: str
    event: StoryArcBeatEvent
    relationships: list[StoryArcRelationship]
    historical_contexts: list[HistoricalContextRead]


class StoryArcDetail(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    core_question: str
    estimated_minutes: int = Field(ge=1)
    progress: ProgressKey
    beats: list[StoryArcBeatRead]


class CharacterDetail(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    summary: str
    interpretation: str | None
    identity_tags: list[str]
    faction_name: str | None
    first_appear_chapter: str | None
    sources: list[EvidenceSource] = Field(default_factory=list)


class RelationshipDetail(BaseModel):
    id: uuid.UUID
    source_name: str
    target_name: str
    relation_type: RelationType
    label: str
    summary: str
    stage: str | None
    confidence: float
    sources: list[EvidenceSource] = Field(default_factory=list)


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
