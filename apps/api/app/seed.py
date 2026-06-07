"""Deterministic fictional data for local development and demonstrations."""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

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

DEMO_PREFIX = "[DEMO FICTION]"
SEED_NAMESPACE = uuid.UUID("3f8588cc-65a0-49bb-b53e-2ff99f6b4af8")


@dataclass(frozen=True)
class ChapterSeed:
    slug: str
    title: str
    region: str
    progress: ProgressKey
    rank: int


@dataclass(frozen=True)
class FactionSeed:
    slug: str
    name: str
    chapter_slug: str


@dataclass(frozen=True)
class CharacterSeed:
    slug: str
    name: str
    faction_slug: str
    chapter_slug: str
    importance: int
    spoiler_level: int


@dataclass(frozen=True)
class EventSeed:
    slug: str
    title: str
    chapter_slug: str
    character_slugs: tuple[str, ...]
    faction_slug: str
    sort_order: int
    spoiler_level: int


@dataclass(frozen=True)
class RelationshipSeed:
    source_slug: str
    target_slug: str
    relation_type: RelationType
    chapter_slug: str
    spoiler_level: int
    directional: bool


@dataclass(frozen=True)
class SeedStats:
    chapters: int
    factions: int
    characters: int
    relationships: int
    events: int
    sources: int


class SeedValidationError(ValueError):
    pass


class Slugged(Protocol):
    slug: str


CHAPTERS = (
    ChapterSeed("demo-start", "演示卷一：雾渡", "雾渡村", ProgressKey.START, 0),
    ChapterSeed("demo-qinghe", "演示卷二：青川", "青川", ProgressKey.QINGHE, 10),
    ChapterSeed("demo-kaifeng", "演示卷三：景城", "景城", ProgressKey.KAIFENG, 20),
    ChapterSeed("demo-current", "演示卷四：星台", "星台", ProgressKey.CURRENT, 90),
    ChapterSeed(
        "demo-unrestricted",
        "演示卷五：终局",
        "无名原",
        ProgressKey.UNRESTRICTED,
        100,
    ),
)

FACTIONS = (
    FactionSeed("demo-canglan", "沧澜社", "demo-start"),
    FactionSeed("demo-chizhu", "赤烛盟", "demo-qinghe"),
    FactionSeed("demo-mingjing", "明镜司", "demo-kaifeng"),
    FactionSeed("demo-yeyu", "夜雨台", "demo-current"),
    FactionSeed("demo-wuming", "无名客栈", "demo-unrestricted"),
)

_CHARACTER_NAMES = (
    ("陆行舟", "桑晚", "石伯", "阿禾"),
    ("顾青崖", "温九", "秦照", "柳三娘"),
    ("宋执镜", "苏悬壶", "吴砺", "空明"),
    ("乐无忧", "白策", "燕七", "唐木"),
    ("玄客", "铁衣", "归鸿", "说书人"),
)


def _slug(index: int, offset: int) -> str:
    return f"demo-character-{index + 1:02d}-{offset + 1:02d}"


CHARACTERS = tuple(
    CharacterSeed(
        slug=_slug(chapter_index, offset),
        name=name,
        faction_slug=FACTIONS[(chapter_index + offset) % len(FACTIONS)].slug,
        chapter_slug=chapter.slug,
        importance=5 if offset == 0 else max(1, 4 - offset),
        spoiler_level=min(3, chapter_index),
    )
    for chapter_index, (chapter, names) in enumerate(
        zip(CHAPTERS, _CHARACTER_NAMES, strict=True)
    )
    for offset, name in enumerate(names)
)

EVENTS = tuple(
    EventSeed(
        slug=f"demo-event-{chapter_index + 1:02d}-{offset + 1:02d}",
        title=f"{DEMO_PREFIX} {chapter.title}事件{offset + 1}",
        chapter_slug=chapter.slug,
        character_slugs=(
            _slug(chapter_index, offset),
            _slug(chapter_index, (offset + 1) % 4),
        ),
        faction_slug=FACTIONS[chapter_index].slug,
        sort_order=offset,
        spoiler_level=min(3, chapter_index),
    )
    for chapter_index, chapter in enumerate(CHAPTERS)
    for offset in range(2)
)

_RELATION_TYPES = tuple(RelationType)
RELATIONSHIPS = tuple(
    RelationshipSeed(
        source_slug=CHARACTERS[index].slug,
        target_slug=CHARACTERS[(index + step) % len(CHARACTERS)].slug,
        relation_type=_RELATION_TYPES[index % len(_RELATION_TYPES)],
        chapter_slug=CHARACTERS[max(index, (index + step) % len(CHARACTERS))].chapter_slug,
        spoiler_level=max(
            CHARACTERS[index].spoiler_level,
            CHARACTERS[(index + step) % len(CHARACTERS)].spoiler_level,
        ),
        directional=index % 3 != 0,
    )
    for step, count in ((1, 20), (5, 10))
    for index in range(count)
)


def stable_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}")


def relationship_key(seed: RelationshipSeed) -> str:
    return (
        f"{seed.source_slug}:{seed.target_slug}:"
        f"{seed.relation_type}:{seed.chapter_slug}"
    )


def validate_seed() -> None:
    errors: list[str] = []
    if len(CHAPTERS) < 5 or len(FACTIONS) < 5:
        errors.append("at least five chapters and factions are required")
    if len(CHARACTERS) < 20 or len(RELATIONSHIPS) < 30 or len(EVENTS) < 10:
        errors.append("demo entity minimums are not satisfied")

    chapter_slugs = {item.slug for item in CHAPTERS}
    faction_slugs = {item.slug for item in FACTIONS}
    character_slugs = {item.slug for item in CHARACTERS}
    event_slugs = {item.slug for item in EVENTS}
    if len(chapter_slugs) != len(CHAPTERS):
        errors.append("chapter slugs must be unique")
    if len(faction_slugs) != len(FACTIONS):
        errors.append("faction slugs must be unique")
    if len(character_slugs) != len(CHARACTERS):
        errors.append("character slugs must be unique")
    if len(event_slugs) != len(EVENTS):
        errors.append("event slugs must be unique")

    for faction in FACTIONS:
        if faction.chapter_slug not in chapter_slugs:
            errors.append(f"missing faction chapter: {faction.chapter_slug}")
    for character in CHARACTERS:
        if character.chapter_slug not in chapter_slugs:
            errors.append(f"missing character chapter: {character.chapter_slug}")
        if character.faction_slug not in faction_slugs:
            errors.append(f"missing character faction: {character.faction_slug}")
        if not 0 <= character.spoiler_level <= 3:
            errors.append(f"invalid character spoiler level: {character.slug}")
    for event in EVENTS:
        if event.chapter_slug not in chapter_slugs:
            errors.append(f"missing event chapter: {event.chapter_slug}")
        if event.faction_slug not in faction_slugs:
            errors.append(f"missing event faction: {event.faction_slug}")
        if not set(event.character_slugs) <= character_slugs:
            errors.append(f"missing event character: {event.slug}")

    identities: set[tuple[str, str, RelationType, str]] = set()
    for relationship in RELATIONSHIPS:
        identity = (
            relationship.source_slug,
            relationship.target_slug,
            relationship.relation_type,
            relationship.chapter_slug,
        )
        if relationship.source_slug == relationship.target_slug:
            errors.append(f"self relationship: {relationship.source_slug}")
        if identity in identities:
            errors.append(f"duplicate relationship: {identity}")
        identities.add(identity)
        if relationship.source_slug not in character_slugs:
            errors.append(f"missing relationship source: {relationship.source_slug}")
        if relationship.target_slug not in character_slugs:
            errors.append(f"missing relationship target: {relationship.target_slug}")
        if relationship.chapter_slug not in chapter_slugs:
            errors.append(f"missing relationship chapter: {relationship.chapter_slug}")
        if not 0 <= relationship.spoiler_level <= 3:
            errors.append(f"invalid relationship spoiler level: {identity}")
    if errors:
        raise SeedValidationError("; ".join(errors))


def _existing_by_slug[T: Slugged](
    db: Session,
    model: type[T],
    slug_column: InstrumentedAttribute[str],
    slugs: set[str],
) -> dict[str, T]:
    return {
        row.slug: row
        for row in db.scalars(select(model).where(slug_column.in_(slugs))).all()
    }


def seed_demo(db: Session) -> SeedStats:
    validate_seed()
    chapters = _existing_by_slug(
        db, Chapter, Chapter.slug, {item.slug for item in CHAPTERS}
    )
    for order, chapter_seed in enumerate(CHAPTERS):
        if chapter_seed.slug not in chapters:
            chapter = Chapter(
                id=stable_id("chapter", chapter_seed.slug),
                slug=chapter_seed.slug,
                title=f"{DEMO_PREFIX} {chapter_seed.title}",
                region=chapter_seed.region,
                sort_order=order,
                progress_key=chapter_seed.progress,
                progress_rank=chapter_seed.rank,
                status=ContentStatus.PUBLISHED,
            )
            db.add(chapter)
            chapters[chapter_seed.slug] = chapter
    db.flush()

    factions = _existing_by_slug(
        db, Faction, Faction.slug, {item.slug for item in FACTIONS}
    )
    for faction_seed in FACTIONS:
        if faction_seed.slug not in factions:
            faction = Faction(
                id=stable_id("faction", faction_seed.slug),
                slug=faction_seed.slug,
                name=f"{faction_seed.name}（演示）",
                faction_type="demo",
                summary=f"{DEMO_PREFIX} 用于验证势力筛选的虚构组织。",
                spoiler_level=min(
                    3, chapters[faction_seed.chapter_slug].progress_rank // 10
                ),
                visible_after_chapter_id=chapters[faction_seed.chapter_slug].id,
                status=ContentStatus.PUBLISHED,
            )
            db.add(faction)
            factions[faction_seed.slug] = faction
    db.flush()

    characters = _existing_by_slug(
        db, Character, Character.slug, {item.slug for item in CHARACTERS}
    )
    for character_seed in CHARACTERS:
        if character_seed.slug not in characters:
            character = Character(
                id=stable_id("character", character_seed.slug),
                slug=character_seed.slug,
                name=f"{character_seed.name}（演示）",
                summary=f"{DEMO_PREFIX} 用于验证剧情关系图谱的虚构角色。",
                interpretation="仅作结构与交互演示，不对应游戏设定。",
                identity_tags=[
                    "演示角色",
                    f"剧透等级{character_seed.spoiler_level}",
                ],
                faction_id=factions[character_seed.faction_slug].id,
                importance=character_seed.importance,
                spoiler_level=character_seed.spoiler_level,
                first_appear_chapter_id=chapters[character_seed.chapter_slug].id,
                visible_after_chapter_id=chapters[character_seed.chapter_slug].id,
                status=ContentStatus.PUBLISHED,
            )
            character.aliases.append(
                CharacterAlias(
                    id=stable_id("alias", character_seed.slug),
                    alias=f"演示代号-{character_seed.name}",
                )
            )
            db.add(character)
            characters[character_seed.slug] = character
    db.flush()

    events = _existing_by_slug(
        db, StoryEvent, StoryEvent.slug, {item.slug for item in EVENTS}
    )
    for event_seed in EVENTS:
        if event_seed.slug not in events:
            story_event = StoryEvent(
                id=stable_id("event", event_seed.slug),
                slug=event_seed.slug,
                title=event_seed.title,
                summary=f"{DEMO_PREFIX} 用于验证时间线排序与进度过滤的虚构事件。",
                impact="该事件只用于演示关系变化和事件影响字段。",
                chapter_id=chapters[event_seed.chapter_slug].id,
                sort_order=event_seed.sort_order,
                spoiler_level=event_seed.spoiler_level,
                visible_after_chapter_id=chapters[event_seed.chapter_slug].id,
                status=ContentStatus.PUBLISHED,
                characters=[
                    characters[slug] for slug in event_seed.character_slugs
                ],
                factions=[factions[event_seed.faction_slug]],
            )
            db.add(story_event)
            events[event_seed.slug] = story_event
    db.flush()

    existing_relationships = {
        relationship.id
        for relationship in db.scalars(
            select(Relationship).where(
                Relationship.id.in_(
                    [
                        stable_id(
                            "relationship",
                            relationship_key(relationship_seed),
                        )
                        for relationship_seed in RELATIONSHIPS
                    ]
                )
            )
        ).all()
    }
    for index, relationship_seed in enumerate(RELATIONSHIPS):
        key = relationship_key(relationship_seed)
        relationship_id = stable_id("relationship", key)
        if relationship_id not in existing_relationships:
            relationship = Relationship(
                id=relationship_id,
                source_character_id=characters[relationship_seed.source_slug].id,
                target_character_id=characters[relationship_seed.target_slug].id,
                relation_type=relationship_seed.relation_type,
                label=f"演示关系 {index + 1}",
                summary=f"{DEMO_PREFIX} 用于验证关系类型与路径查询的虚构关系。",
                stage=chapters[relationship_seed.chapter_slug].title,
                is_directional=relationship_seed.directional,
                chapter_id=chapters[relationship_seed.chapter_slug].id,
                visible_after_chapter_id=chapters[relationship_seed.chapter_slug].id,
                spoiler_level=relationship_seed.spoiler_level,
                confidence=0.8,
                status=ContentStatus.PUBLISHED,
                events=[events[EVENTS[index % len(EVENTS)].slug]],
            )
            db.add(relationship)

    for source_seed in EVENTS:
        source_id = stable_id("source", source_seed.slug)
        if db.get(Source, source_id) is None:
            db.add(
                Source(
                    id=source_id,
                    source_type=SourceType.PLAYER_NOTE,
                    title=f"{DEMO_PREFIX} {source_seed.title}来源说明",
                    reference=None,
                    note="演示来源，不可作为正式内容依据。",
                    event_id=events[source_seed.slug].id,
                )
            )
    db.flush()
    return SeedStats(
        chapters=len(CHAPTERS),
        factions=len(FACTIONS),
        characters=len(CHARACTERS),
        relationships=len(RELATIONSHIPS),
        events=len(EVENTS),
        sources=len(EVENTS),
    )


def main() -> None:
    with SessionLocal() as db:
        try:
            stats = seed_demo(db)
            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"Demo seed failed: {exc}", file=sys.stderr)
            raise
    print(f"Demo seed ready: {stats}")


if __name__ == "__main__":
    main()
