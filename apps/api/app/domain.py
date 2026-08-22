from enum import StrEnum


class ProgressKey(StrEnum):
    START = "start"
    QINGHE = "qinghe"
    KAIFENG = "kaifeng"
    CURRENT = "current"
    UNRESTRICTED = "unrestricted"


PROGRESS_RANK: dict[ProgressKey, int] = {
    ProgressKey.START: 0,
    ProgressKey.QINGHE: 10,
    ProgressKey.KAIFENG: 20,
    ProgressKey.CURRENT: 90,
    ProgressKey.UNRESTRICTED: 100,
}


class RelationType(StrEnum):
    MENTOR = "mentor"
    FAMILY = "family"
    ENEMY = "enemy"
    ALLY = "ally"
    OLD_ACQUAINTANCE = "old_acquaintance"
    EXPLOITATION = "exploitation"
    HIERARCHY = "hierarchy"
    SAME_SECT = "same_sect"
    INTEREST = "interest"
    HIDDEN = "hidden"


class SubmissionType(StrEnum):
    RELATIONSHIP = "relationship"
    EVENT = "event"
    INTERPRETATION = "interpretation"
    CORRECTION = "correction"


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SourceType(StrEnum):
    PLAYER_NOTE = "player_note"
    QUEST_REFERENCE = "quest_reference"
    OFFICIAL_REFERENCE = "official_reference"
    COMMUNITY_ANALYSIS = "community_analysis"


class StoryBeatRole(StrEnum):
    SETUP = "setup"
    CLUE = "clue"
    ESCALATION = "escalation"
    TURNING_POINT = "turning_point"
    CONSEQUENCE = "consequence"
    RESOLUTION = "resolution"


class HistoricalFactKind(StrEnum):
    WORK_FACT = "work_fact"
    HISTORICAL_FACT = "historical_fact"
    CREDIBLE_PARALLEL = "credible_parallel"
    EDITORIAL_INFERENCE = "editorial_inference"


class HistoricalRelationKind(StrEnum):
    SETTING = "setting"
    INSPIRED_BY = "inspired_by"
    PARALLEL = "parallel"
    CONTRAST = "contrast"
    FICTIONALIZED = "fictionalized"


class HistoricalReferenceType(StrEnum):
    PRIMARY_SOURCE = "primary_source"
    SCHOLARLY_RESEARCH = "scholarly_research"
    INSTITUTIONAL_REFERENCE = "institutional_reference"


class CanonicalStoryNodeType(StrEnum):
    """v1 canonical taxonomy (frozen contract rev 2): main-line backbone only."""

    CHAPTER = "chapter"
    MAIN_PART = "main_part"
    MAIN_QUEST = "main_quest"


class CanonicalMappingKind(StrEnum):
    """Link cardinality between canonical nodes and StoryEvents (frozen).

    EDITORIAL_ONLY is intentionally NOT a mapping kind: editorial-only events
    simply carry zero canonical links (derived audit state).
    """

    EXACT = "exact"
    MERGED = "merged"
    SPLIT = "split"


class CanonicalVerificationState(StrEnum):
    VERIFIED = "verified"
    PROVISIONAL = "provisional"
    SOURCE_CONFLICT = "source_conflict"
    UNRESOLVED = "unresolved"


class CanonicalSpine(StrEnum):
    MAIN = "main"
    SECONDARY = "secondary"


class CanonicalSourceKind(StrEnum):
    """Provenance source kinds (alignment plan Level 1-2)."""

    OFFICIAL = "official"
    WALKTHROUGH = "walkthrough"
    WIKI = "wiki"
    PLAYER = "player"
    IN_GAME = "in_game"


class CanonicalEvidenceRole(StrEnum):
    """Which node field a provenance entry supports (frozen contract v0.1)."""

    IDENTITY = "identity"
    TITLE = "title"
    HIERARCHY = "hierarchy"
    ORDER = "order"
    TYPE = "type"
    GAME_ID = "game_id"
    GENERAL = "general"
