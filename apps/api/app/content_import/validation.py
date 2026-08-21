"""Structural and referential validation for content datasets."""

from __future__ import annotations

import json
from collections.abc import Hashable, Sequence
from pathlib import Path

from .models import ContentDataset, ContentValidationError


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

