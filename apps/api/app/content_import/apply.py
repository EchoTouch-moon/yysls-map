"""Transactional upsert of a validated dataset into the database."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.domain import ContentStatus, ProgressKey
from app.models import (
    CanonicalStoryEventLink,
    CanonicalStoryNode,
    Chapter,
    Character,
    CharacterAlias,
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

from .models import (
    CanonicalDataset,
    CanonicalImportStats,
    ContentDataset,
    ContentValidationError,
    ImportStats,
    SourceItem,
    stable_content_id,
)


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


def _clear_canonical(db: Session) -> None:
    db.execute(delete(CanonicalStoryEventLink))
    db.execute(delete(CanonicalStoryNode))
    db.flush()


def import_canonical_dataset(
    db: Session,
    dataset: CanonicalDataset,
    *,
    replace_existing: bool = False,
) -> CanonicalImportStats:
    """Transactional upsert of a canonical dataset (frozen contract rev 2).

    Additive by design: touches only canonical_story_nodes and
    canonical_story_event_links. StoryEvent resolution happens by slug; a
    missing event aborts the import (fail-closed). Cardinality and publication
    invariants are enforced by validate_canonical_dataset before any write.
    """
    from .validation import validate_canonical_dataset

    validate_canonical_dataset(dataset)
    if replace_existing:
        _clear_canonical(db)

    nodes: dict[str, CanonicalStoryNode] = {}
    for item in dataset.nodes:
        row_id = stable_content_id("canonical-node", item.canonical_key)
        node = db.get(CanonicalStoryNode, row_id)
        if node is None:
            node = CanonicalStoryNode(id=row_id)
            db.add(node)
        node.canonical_key = item.canonical_key
        node.native_id = item.native_id
        node.title = item.title
        node.node_type = item.node_type
        node.region = item.region
        node.chapter_slug = item.chapter_slug
        node.sort_order = item.sort_order
        node.spine = item.spine
        node.provenance = [entry.model_dump() for entry in item.provenance]
        node.verification_state = item.verification_state
        node.status = item.status
        nodes[item.canonical_key] = node
    db.flush()

    for key, node in nodes.items():
        item = next(item for item in dataset.nodes if item.canonical_key == key)
        node.parent_id = nodes[item.parent_key].id if item.parent_key else None
    db.flush()

    events_by_slug = {
        event.slug: event
        for event in db.scalars(select(StoryEvent)).all()
    }
    missing_events = sorted(
        {link.event_slug for link in dataset.links} - set(events_by_slug)
    )
    if missing_events:
        raise ContentValidationError(
            [f"canonical links reference missing events: {', '.join(missing_events)}"]
        )

    for link_item in dataset.links:
        node = nodes[link_item.node_key]
        event = events_by_slug[link_item.event_slug]
        row_id = stable_content_id(
            "canonical-link", f"{link_item.node_key}:{link_item.event_slug}"
        )
        link = db.get(CanonicalStoryEventLink, row_id)
        if link is None:
            link = CanonicalStoryEventLink(id=row_id)
            db.add(link)
        link.canonical_node_id = node.id
        link.story_event_id = event.id
        link.mapping_kind = link_item.mapping_kind
        link.sort_order = link_item.sort_order
        link.is_primary = link_item.is_primary
        link.note = link_item.note
    db.flush()

    return CanonicalImportStats(nodes=len(nodes), links=len(dataset.links))
