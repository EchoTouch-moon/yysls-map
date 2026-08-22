"""Structural and referential validation for content datasets."""

from __future__ import annotations

import json
from collections.abc import Hashable, Sequence
from pathlib import Path

from app.domain import (
    CanonicalEvidenceRole,
    CanonicalMappingKind,
    CanonicalVerificationState,
    ContentStatus,
)

from .models import (
    CanonicalDataset,
    CanonicalEventLinkItem,
    ContentDataset,
    ContentValidationError,
)


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


def validate_canonical_dataset(dataset: CanonicalDataset) -> None:
    """Structural validation for a canonical dataset (frozen contract rev 2).

    Implements the C2 gates that are checkable without a database:
    - C2-G4 publication safety: UNRESOLVED / PROVISIONAL nodes cannot be PUBLISHED;
    - C2-G5 mapping cardinality invariants (EXACT/MERGED/SPLIT + no complex N:M);
    - C2-G6 provenance: published nodes need identity evidence; refs non-empty.
    Referential checks that need the database (parent exists, event exists) are
    performed at apply time.
    """
    errors: list[str] = []
    if dataset.schema_version != "0.1":
        errors.append(f"unsupported canonical schema version: {dataset.schema_version}")

    node_keys = [item.canonical_key for item in dataset.nodes]
    duplicate_keys = sorted(_duplicates(node_keys))
    if duplicate_keys:
        errors.append(f"duplicate canonical keys: {', '.join(duplicate_keys)}")

    key_set = set(node_keys)
    parent_keys = [item.parent_key for item in dataset.nodes if item.parent_key is not None]
    missing_parents = sorted(set(parent_keys) - key_set)
    if missing_parents:
        errors.append(f"parent_key references missing nodes: {', '.join(missing_parents)}")

    for item in dataset.nodes:
        if (
            item.verification_state
            in (CanonicalVerificationState.UNRESOLVED, CanonicalVerificationState.PROVISIONAL)
            and item.status is ContentStatus.PUBLISHED
        ):
            errors.append(
                f"node {item.canonical_key}: {item.verification_state.value} "
                "cannot be PUBLISHED (C2-G4)"
            )
        # H-C2-1 (frozen C2-G6): GENERAL may supplement but cannot replace
        # IDENTITY for a published node's identity evidence.
        if item.status is ContentStatus.PUBLISHED and not any(
            entry.evidence_role is CanonicalEvidenceRole.IDENTITY
            for entry in item.provenance
        ):
            errors.append(
                f"node {item.canonical_key}: published node needs IDENTITY evidence (C2-G6)"
            )
        if any(not entry.ref.strip() for entry in item.provenance):
            errors.append(f"node {item.canonical_key}: empty provenance ref is not allowed (C2-G6)")

    link_pairs = [(item.node_key, item.event_slug) for item in dataset.links]
    duplicate_pairs = sorted(_duplicate_string_pairs(link_pairs))
    if duplicate_pairs:
        errors.append(
            "duplicate canonical links: "
            + ", ".join(f"{node}:{event}" for node, event in duplicate_pairs)
        )

    link_node_keys = [item.node_key for item in dataset.links]
    missing_link_nodes = sorted(set(link_node_keys) - key_set)
    if missing_link_nodes:
        errors.append(f"link references missing nodes: {', '.join(missing_link_nodes)}")

    # --- C2-G5 mapping cardinality invariants ---
    links_by_event: dict[str, list[CanonicalEventLinkItem]] = {}
    links_by_node: dict[str, list[CanonicalEventLinkItem]] = {}
    for link in dataset.links:
        links_by_event.setdefault(link.event_slug, []).append(link)
        links_by_node.setdefault(link.node_key, []).append(link)

    # Event side: one link -> EXACT (1:1) or SPLIT (node-side split, each
    # event carries exactly one SPLIT link); many links -> all MERGED.
    for event_slug, links in sorted(links_by_event.items()):
        kinds = {link.mapping_kind for link in links}
        if len(links) == 1:
            if next(iter(kinds)) not in (
                CanonicalMappingKind.EXACT,
                CanonicalMappingKind.SPLIT,
            ):
                errors.append(
                    f"event {event_slug}: single link must be EXACT or SPLIT, "
                    f"got {next(iter(kinds)).value}"
                )
        elif len(links) >= 2 and not all(
            kind is CanonicalMappingKind.MERGED for kind in kinds
        ):
                errors.append(
                    f"event {event_slug}: multi-link event must be all MERGED, got "
                    + ", ".join(sorted(kind.value for kind in kinds))
                )

    # Node side: one link -> EXACT (1:1) or MERGED (event-side merge, each node
    # carries exactly one MERGED link); many links -> all SPLIT.
    for node_key, links in sorted(links_by_node.items()):
        kinds = {link.mapping_kind for link in links}
        if len(links) == 1:
            if next(iter(kinds)) not in (
                CanonicalMappingKind.EXACT,
                CanonicalMappingKind.MERGED,
            ):
                errors.append(
                    f"node {node_key}: single link must be EXACT or MERGED, "
                    f"got {next(iter(kinds)).value}"
                )
        elif len(links) >= 2 and not all(
            kind is CanonicalMappingKind.SPLIT for kind in kinds
        ):
                errors.append(
                    f"node {node_key}: multi-link node must be all SPLIT, got "
                    + ", ".join(sorted(kind.value for kind in kinds))
                )

    # complex many-to-many mapping groups are unsupported in v0.1 (frozen rule)
    for event_slug, event_links in links_by_event.items():
        if len(event_links) < 2:
            continue
        for link in event_links:
            if len(links_by_node.get(link.node_key, [])) >= 2:
                errors.append(
                    f"complex N:M mapping group around event {event_slug} / node "
                    f"{link.node_key} is unsupported in v0.1 (frozen rule)"
                )
                break

    if errors:
        raise ContentValidationError(errors)


def load_canonical_dataset(path: Path) -> CanonicalDataset:
    """Load and validate a canonical dataset file (frozen contract v0.1)."""
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    dataset = CanonicalDataset.model_validate(payload)
    validate_canonical_dataset(dataset)
    return dataset
