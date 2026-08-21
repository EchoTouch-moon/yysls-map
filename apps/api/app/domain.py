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
