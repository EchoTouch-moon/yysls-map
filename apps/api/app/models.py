import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, MappedColumn, mapped_column, relationship

from app.db import Base, TimestampMixin
from app.domain import (
    CanonicalMappingKind,
    CanonicalSpine,
    CanonicalStoryNodeType,
    CanonicalVerificationState,
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


def uuid_pk() -> MappedColumn[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


event_characters = Table(
    "event_characters",
    Base.metadata,
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("story_events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "character_id",
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_factions = Table(
    "event_factions",
    Base.metadata,
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("story_events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "faction_id",
        UUID(as_uuid=True),
        ForeignKey("factions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

relationship_events = Table(
    "relationship_events",
    Base.metadata,
    Column(
        "relationship_id",
        UUID(as_uuid=True),
        ForeignKey("relationships.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("story_events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

historical_context_references = Table(
    "historical_context_references",
    Base.metadata,
    Column(
        "context_id",
        UUID(as_uuid=True),
        ForeignKey("historical_contexts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "reference_id",
        UUID(as_uuid=True),
        ForeignKey("historical_references.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, unique=True)
    progress_key: Mapped[ProgressKey] = mapped_column(
        Enum(ProgressKey, name="progress_key"), index=True
    )
    progress_rank: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        CheckConstraint("progress_rank >= 0 AND progress_rank <= 100", name="progress_rank_range"),
    )


class Faction(Base, TimestampMixin):
    __tablename__ = "factions"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    faction_type: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL")
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"), default=ContentStatus.DRAFT, index=True
    )

    __table_args__ = (
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
        Index(
            "ix_factions_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    summary: Mapped[str] = mapped_column(Text)
    interpretation: Mapped[str | None] = mapped_column(Text)
    identity_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    faction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("factions.id", ondelete="SET NULL"), index=True
    )
    importance: Mapped[int] = mapped_column(Integer, default=1)
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    first_appear_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL")
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    faction: Mapped[Faction | None] = relationship()
    aliases: Mapped[list["CharacterAlias"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("importance >= 1 AND importance <= 5", name="importance_range"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
        Index(
            "ix_characters_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class CharacterAlias(Base):
    __tablename__ = "character_aliases"

    id: Mapped[uuid.UUID] = uuid_pk()
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    alias: Mapped[str] = mapped_column(String(120), index=True)
    character: Mapped[Character] = relationship(back_populates="aliases")

    __table_args__ = (UniqueConstraint("character_id", "alias"),)


class StoryEvent(Base, TimestampMixin):
    __tablename__ = "story_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    summary: Mapped[str] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id", ondelete="RESTRICT"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer)
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL")
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    chapter: Mapped[Chapter] = relationship(foreign_keys=[chapter_id])
    characters: Mapped[list[Character]] = relationship(secondary=event_characters)
    factions: Mapped[list[Faction]] = relationship(secondary=event_factions)

    __table_args__ = (
        UniqueConstraint("chapter_id", "sort_order"),
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
        Index(
            "ix_story_events_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )


class Relationship(Base, TimestampMixin):
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    target_character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    relation_type: Mapped[RelationType] = mapped_column(
        Enum(RelationType, name="relation_type"), index=True
    )
    label: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(String(120))
    is_directional: Mapped[bool] = mapped_column(default=True)
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL")
    )
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=1)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    source: Mapped[Character] = relationship(foreign_keys=[source_character_id])
    target: Mapped[Character] = relationship(foreign_keys=[target_character_id])
    events: Mapped[list[StoryEvent]] = relationship(secondary=relationship_events)

    __table_args__ = (
        CheckConstraint("source_character_id <> target_character_id", name="different_characters"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        UniqueConstraint(
            "source_character_id",
            "target_character_id",
            "relation_type",
            "chapter_id",
            name="uq_relationship_identity",
        ),
        Index("ix_relationship_endpoints", "source_character_id", "target_character_id"),
    )


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"))
    title: Mapped[str] = mapped_column(String(200))
    reference: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), index=True
    )
    faction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("factions.id", ondelete="CASCADE"), index=True
    )
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("story_events.id", ondelete="CASCADE"), index=True
    )
    relationship_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), index=True
    )

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(chapter_id, faction_id, character_id, event_id, relationship_id) = 1",
            name="exactly_one_subject",
        ),
    )


class StoryArc(Base, TimestampMixin):
    __tablename__ = "story_arcs"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    core_question: Mapped[str] = mapped_column(Text)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )
    beats: Mapped[list["StoryArcBeat"]] = relationship(
        back_populates="arc", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("estimated_minutes >= 1", name="estimated_minutes_positive"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
    )


class StoryArcBeat(Base, TimestampMixin):
    __tablename__ = "story_arc_beats"

    id: Mapped[uuid.UUID] = uuid_pk()
    arc_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story_arcs.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story_events.id", ondelete="CASCADE"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer)
    role: Mapped[StoryBeatRole] = mapped_column(Enum(StoryBeatRole, name="story_beat_role"))
    guide: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    bridge: Mapped[str] = mapped_column(Text)
    next_question: Mapped[str] = mapped_column(Text)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    arc: Mapped[StoryArc] = relationship(back_populates="beats")
    event: Mapped[StoryEvent] = relationship()

    __table_args__ = (
        UniqueConstraint("arc_id", "sort_order", name="uq_story_arc_beat_order"),
        UniqueConstraint("arc_id", "event_id", name="uq_story_arc_beat_event"),
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
    )


class CanonicalStoryNode(Base, TimestampMixin):
    """Game-native story coordinate (frozen contract v0.1 rev 2).

    Holds only game-fact structure: identity, hierarchy, order, provenance and
    verification state. It must not depend on StoryEvent surviving (C1-G1).
    """

    __tablename__ = "canonical_story_nodes"

    id: Mapped[uuid.UUID] = uuid_pk()
    canonical_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    native_id: Mapped[str | None] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(240))
    node_type: Mapped[CanonicalStoryNodeType] = mapped_column(
        Enum(CanonicalStoryNodeType, name="canonical_story_node_type"), index=True
    )
    region: Mapped[str] = mapped_column(String(120))
    chapter_slug: Mapped[str] = mapped_column(String(80), index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("canonical_story_nodes.id", ondelete="RESTRICT"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer)
    spine: Mapped[CanonicalSpine] = mapped_column(
        Enum(CanonicalSpine, name="canonical_spine"), default=CanonicalSpine.MAIN
    )
    provenance: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    verification_state: Mapped[CanonicalVerificationState] = mapped_column(
        Enum(CanonicalVerificationState, name="canonical_verification_state"), index=True
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    parent: Mapped["CanonicalStoryNode | None"] = relationship(remote_side=[id])
    children: Mapped[list["CanonicalStoryNode"]] = relationship(back_populates="parent")
    event_links: Mapped[list["CanonicalStoryEventLink"]] = relationship(
        back_populates="node", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        Index(
            "ix_canonical_story_nodes_parent_order",
            "parent_id",
            "sort_order",
            unique=True,
            postgresql_where=text("parent_id IS NOT NULL"),
        ),
    )


class CanonicalStoryEventLink(Base, TimestampMixin):
    """Mapping between a canonical node and a StoryEvent (frozen contract).

    mapping_kind is EXACT / MERGED / SPLIT only; editorial-only events carry no
    link at all (C1-G2). Cardinality invariants are enforced by the import
    validator (C2-G5), not by the database alone.
    """

    __tablename__ = "canonical_story_event_links"

    id: Mapped[uuid.UUID] = uuid_pk()
    canonical_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("canonical_story_nodes.id", ondelete="CASCADE"), index=True
    )
    story_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story_events.id", ondelete="CASCADE"), index=True
    )
    mapping_kind: Mapped[CanonicalMappingKind] = mapped_column(
        Enum(CanonicalMappingKind, name="canonical_mapping_kind"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(default=False)
    note: Mapped[str | None] = mapped_column(Text)

    node: Mapped[CanonicalStoryNode] = relationship(back_populates="event_links")
    event: Mapped[StoryEvent] = relationship()

    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        UniqueConstraint(
            "canonical_node_id",
            "story_event_id",
            name="uq_canonical_link_node_event",
        ),
    )


class HistoricalReference(Base, TimestampMixin):
    __tablename__ = "historical_references"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    reference_type: Mapped[HistoricalReferenceType] = mapped_column(
        Enum(HistoricalReferenceType, name="historical_reference_type")
    )
    title: Mapped[str] = mapped_column(String(240))
    publisher: Mapped[str] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(String(500))
    locator: Mapped[str | None] = mapped_column(String(240))
    accessed_at: Mapped[date] = mapped_column(Date)


class HistoricalContext(Base, TimestampMixin):
    __tablename__ = "historical_contexts"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    period_label: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    fact_kind: Mapped[HistoricalFactKind] = mapped_column(
        Enum(HistoricalFactKind, name="historical_fact_kind"), index=True
    )
    boundary_note: Mapped[str] = mapped_column(Text)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )
    references: Mapped[list[HistoricalReference]] = relationship(
        secondary=historical_context_references
    )

    __table_args__ = (
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
    )


class EventHistoricalLink(Base, TimestampMixin):
    __tablename__ = "event_historical_links"

    id: Mapped[uuid.UUID] = uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story_events.id", ondelete="CASCADE"), index=True
    )
    context_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("historical_contexts.id", ondelete="CASCADE"), index=True
    )
    relation_kind: Mapped[HistoricalRelationKind] = mapped_column(
        Enum(HistoricalRelationKind, name="historical_relation_kind")
    )
    editorial_note: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)
    visible_after_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True
    )
    spoiler_level: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", create_type=False),
        default=ContentStatus.DRAFT,
        index=True,
    )

    event: Mapped[StoryEvent] = relationship()
    context: Mapped[HistoricalContext] = relationship()

    __table_args__ = (
        UniqueConstraint("event_id", "context_id", name="uq_event_historical_context"),
        UniqueConstraint("event_id", "sort_order", name="uq_event_historical_sort_order"),
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        CheckConstraint("spoiler_level >= 0 AND spoiler_level <= 3", name="spoiler_level_range"),
    )


class ContentImportRun(Base):
    __tablename__ = "content_import_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[str] = mapped_column(String(160), index=True)
    dataset_title: Mapped[str] = mapped_column(String(240))
    schema_version: Mapped[str] = mapped_column(String(40))
    collected_at: Mapped[date] = mapped_column(Date)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    replaced_existing: Mapped[bool] = mapped_column(default=False)
    stats: Mapped[dict[str, int]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    submission_type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, name="submission_type"), index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    contact: Mapped[str | None] = mapped_column(String(200))
    source_note: Mapped[str] = mapped_column(Text)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        default=SubmissionStatus.PENDING,
        index=True,
    )
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(String(120))


class AIDraftRun(Base):
    __tablename__ = "ai_draft_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    output: Mapped[dict[str, Any]] = mapped_column(JSON)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (CheckConstraint("duration_ms >= 0", name="duration_nonnegative"),)


class RateLimitHit(Base):
    __tablename__ = "rate_limit_hits"

    id: Mapped[uuid.UUID] = uuid_pk()
    bucket_key: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_rate_limit_hits_bucket_key_created_at", "bucket_key", "created_at"),
    )
