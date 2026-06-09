from pathlib import Path

from app.content_import import load_dataset, stable_content_id
from app.domain import ProgressKey

DATASET_PATH = Path(__file__).parents[3] / "docs" / "yysls-qinghe-v4.json"


def test_qinghe_dataset_matches_extended_release_contract() -> None:
    dataset = load_dataset(DATASET_PATH)

    assert dataset.schema_version == "1.0"
    assert len(dataset.chapters) == 1
    assert len(dataset.factions) == 10
    assert len(dataset.characters) == 39
    assert len(dataset.events) == 27
    assert len(dataset.relationships) == 29
    assert len(dataset.sources) == 21


def test_qinghe_relationship_event_references_exist() -> None:
    dataset = load_dataset(DATASET_PATH)
    event_ids = {event.id for event in dataset.events}

    for relationship in dataset.relationships:
        assert set(relationship.event_ids) <= event_ids


def test_only_prologue_events_are_visible_at_start() -> None:
    dataset = load_dataset(DATASET_PATH)

    assert all(
        event.part == 0
        for event in dataset.events
        if event.visible_after_progress is ProgressKey.START
    )


def test_stable_content_ids_are_deterministic_and_scoped() -> None:
    first = stable_content_id("character", "protagonist")

    assert first == stable_content_id("character", "protagonist")
    assert first != stable_content_id("event", "protagonist")
