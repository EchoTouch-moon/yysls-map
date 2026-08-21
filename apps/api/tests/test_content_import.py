import os
import uuid
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.content_import as import_module
from app.api.contracts import CharacterDetail, RelationshipDetail
from app.api.routes.details import character_detail, relationship_detail
from app.api.routes.graph import get_graph
from app.api.routes.story_arcs import get_story_arc, list_story_arcs
from app.api.routes.timeline import get_timeline
from app.content_import import (
    ContentValidationError,
    import_dataset,
    load_dataset,
    main,
    run_import,
    stable_content_id,
    validate_dataset,
)
from app.db import SessionLocal
from app.domain import ContentStatus, ProgressKey, SourceType
from app.models import (
    Chapter,
    Character,
    ContentImportRun,
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
from app.services.content import get_source_by_id_published
from app.services.spoiler import context_for

DATASET_PATH = Path(__file__).parents[3] / "content" / "yysls-qinghe-v4.json"


def test_qinghe_dataset_matches_extended_release_contract() -> None:
    dataset = load_dataset(DATASET_PATH)

    assert dataset.schema_version == "1.1"
    assert len(dataset.chapters) == 1
    assert len(dataset.factions) == 10
    assert len(dataset.characters) == 39
    assert len(dataset.events) == 27
    assert len(dataset.relationships) == 29
    assert len(dataset.sources) == 24
    assert sum(1 for s in dataset.sources if s.source_type == SourceType.OFFICIAL_REFERENCE) == 3
    assert len(dataset.story_arcs) == 1
    assert len(dataset.story_arcs[0].beats) == 10
    assert dataset.story_arcs[0].estimated_minutes == 12
    assert len(dataset.historical_references) == 8
    assert len(dataset.historical_contexts) == 5
    assert len(dataset.event_historical_links) == 4
    assert all(context.reference_ids for context in dataset.historical_contexts)


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


def test_validator_rejects_duplicate_ids_and_missing_references() -> None:
    dataset = load_dataset(DATASET_PATH)
    broken_character = dataset.characters[0].model_copy(update={"faction_id": "missing-faction"})
    broken = dataset.model_copy(
        update={
            "characters": [
                broken_character,
                *dataset.characters[1:],
                broken_character,
            ]
        }
    )

    with pytest.raises(ContentValidationError) as exc_info:
        validate_dataset(broken)

    assert "duplicate character IDs" in str(exc_info.value)
    assert "references missing faction" in str(exc_info.value)


def test_validator_rejects_self_relationship_and_unknown_source() -> None:
    dataset = load_dataset(DATASET_PATH)
    relationship = dataset.relationships[0]
    broken_relationship = relationship.model_copy(
        update={
            "target_character_id": relationship.source_character_id,
            "source_ids": ["missing-source"],
        }
    )
    broken = dataset.model_copy(
        update={
            "relationships": [
                broken_relationship,
                *dataset.relationships[1:],
            ]
        }
    )

    with pytest.raises(ContentValidationError) as exc_info:
        validate_dataset(broken)

    assert "references itself" in str(exc_info.value)
    assert "sources references missing IDs: missing-source" in str(exc_info.value)


def test_validator_rejects_unsupported_metadata_and_duplicate_links() -> None:
    dataset = load_dataset(DATASET_PATH)
    chapter = dataset.chapters[0]
    broken = dataset.model_copy(
        update={
            "schema_version": "2.0",
            "dataset": dataset.dataset.model_copy(update={"language": "en-US"}),
            "chapters": [chapter.model_copy(update={"source_ids": [chapter.source_ids[0]] * 2})],
        }
    )

    with pytest.raises(ContentValidationError) as exc_info:
        validate_dataset(broken)

    assert "unsupported schema version" in str(exc_info.value)
    assert "unexpected language" in str(exc_info.value)
    assert "duplicate sources for chapter" in str(exc_info.value)


def test_validator_rejects_broken_story_and_history_links() -> None:
    dataset = load_dataset(DATASET_PATH)
    arc = dataset.story_arcs[0]
    first_beat = arc.beats[0]
    context = dataset.historical_contexts[0]
    broken = dataset.model_copy(
        update={
            "story_arcs": [
                arc.model_copy(
                    update={
                        "beats": [
                            first_beat.model_copy(update={"event_id": "missing-event"}),
                            first_beat,
                        ]
                    }
                )
            ],
            "historical_contexts": [
                context.model_copy(update={"reference_ids": ["missing-reference"]}),
                *dataset.historical_contexts[1:],
            ],
        }
    )

    with pytest.raises(ContentValidationError) as exc_info:
        validate_dataset(broken)

    assert "duplicate beat sort orders" in str(exc_info.value)
    assert "beat events references missing IDs: missing-event" in str(exc_info.value)
    assert "references missing IDs: missing-reference" in str(exc_info.value)


@pytest.mark.parametrize("unsafe_url", ["javascript:alert(1)", "https://"])
def test_historical_reference_rejects_unsafe_url(unsafe_url: str) -> None:
    dataset = load_dataset(DATASET_PATH)
    with pytest.raises(ValidationError, match="absolute http or https"):
        dataset.historical_references[0].model_validate(
            {
                **dataset.historical_references[0].model_dump(mode="json"),
                "url": unsafe_url,
            }
        )


def test_historical_context_requires_at_least_one_reference() -> None:
    dataset = load_dataset(DATASET_PATH)
    with pytest.raises(ValidationError, match="at least 1 item"):
        dataset.historical_contexts[0].model_validate(
            {
                **dataset.historical_contexts[0].model_dump(mode="json"),
                "reference_ids": [],
            }
        )


def test_story_arc_requires_at_least_one_beat() -> None:
    dataset = load_dataset(DATASET_PATH)
    with pytest.raises(ValidationError, match="at least 1 item"):
        dataset.story_arcs[0].model_validate(
            {
                **dataset.story_arcs[0].model_dump(mode="json"),
                "beats": [],
            }
        )


def test_validator_rejects_duplicate_history_link_order_per_event() -> None:
    dataset = load_dataset(DATASET_PATH)
    first, second, *remaining = dataset.event_historical_links
    broken = dataset.model_copy(
        update={
            "event_historical_links": [
                first,
                second.model_copy(update={"sort_order": first.sort_order}),
                *remaining,
            ]
        }
    )

    with pytest.raises(ContentValidationError) as exc_info:
        validate_dataset(broken)

    assert "duplicate event historical link sort orders" in str(exc_info.value)


def test_validate_only_does_not_open_database_session() -> None:
    def fail_session() -> Session:
        raise AssertionError("validate-only must not connect to the database")

    main(
        [str(DATASET_PATH), "--validate-only"],
        session_factory=fail_session,
    )


@pytest.mark.parametrize(
    "arguments",
    [
        ["--replace-existing"],
        ["--replace-existing", "--confirm-replace", "wrong-dataset"],
    ],
)
def test_replace_requires_matching_dataset_confirmation(
    arguments: list[str],
) -> None:
    def fail_session() -> Session:
        raise AssertionError("invalid replacement must fail before connecting")

    with pytest.raises(SystemExit):
        main(
            [str(DATASET_PATH), *arguments],
            session_factory=fail_session,
        )


class FakeSession:
    committed = False
    rolled_back = False

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_dry_run_rolls_back_without_committing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        import_module,
        "run_import",
        lambda *_args, **_kwargs: import_module.ImportStats(
            chapters=1,
            factions=0,
            characters=1,
            events=1,
            relationships=0,
            source_definitions=1,
            source_links=1,
            story_arcs=1,
            story_arc_beats=1,
            historical_references=0,
            historical_contexts=0,
            event_historical_links=0,
        ),
    )

    main(
        [str(DATASET_PATH), "--dry-run"],
        session_factory=lambda: cast(Session, session),
    )

    assert session.rolled_back is True
    assert session.committed is False


def test_failed_import_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def fail_import(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("forced failure")

    monkeypatch.setattr(import_module, "run_import", fail_import)

    with pytest.raises(RuntimeError, match="forced failure"):
        main(
            [str(DATASET_PATH)],
            session_factory=lambda: cast(Session, session),
        )

    assert session.rolled_back is True
    assert session.committed is False


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires a disposable PostgreSQL test database",
)
def test_content_import_postgresql_lifecycle() -> None:
    dataset = load_dataset(DATASET_PATH)
    sentinel_id = uuid.uuid4()

    with SessionLocal() as db:
        max_sort = db.scalar(select(func.max(Chapter.sort_order))) or 0
        db.add(
            Chapter(
                id=sentinel_id,
                slug=f"import-sentinel-{sentinel_id.hex}",
                title="导入保留测试",
                region=None,
                sort_order=max_sort + 500,
                progress_key=ProgressKey.CURRENT,
                progress_rank=90,
                status=ContentStatus.DRAFT,
            )
        )
        db.flush()

        try:
            first = run_import(
                db,
                dataset=dataset,
                dataset_path=DATASET_PATH,
                replace_existing=False,
            )
            assert db.get(Chapter, sentinel_id) is not None
            counts_after_first = {
                model: db.scalar(select(func.count()).select_from(model))
                for model in (
                    Chapter,
                    Faction,
                    Character,
                    StoryEvent,
                    Relationship,
                    Source,
                    StoryArc,
                    StoryArcBeat,
                    HistoricalReference,
                    HistoricalContext,
                    EventHistoricalLink,
                )
            }

            second = import_dataset(db, dataset)
            counts_after_second = {
                model: db.scalar(select(func.count()).select_from(model))
                for model in counts_after_first
            }
            assert second == first
            assert counts_after_second == counts_after_first

            removed_link = dataset.event_historical_links[-1]
            total_links = len(dataset.event_historical_links)
            dataset_without_link = dataset.model_copy(
                update={"event_historical_links": dataset.event_historical_links[:-1]}
            )
            import_dataset(db, dataset_without_link)
            assert (
                db.scalar(select(func.count()).select_from(EventHistoricalLink))
                == total_links - 1
            )
            assert (
                db.get(
                    EventHistoricalLink,
                    stable_content_id("event-historical-link", removed_link.id),
                )
                is None
            )
            import_dataset(db, dataset)
            assert db.scalar(select(func.count()).select_from(EventHistoricalLink)) == total_links

            expected_source_links = sum(
                len(item.source_ids)
                for items in (
                    dataset.chapters,
                    dataset.factions,
                    dataset.characters,
                    dataset.events,
                    dataset.relationships,
                )
                for item in items
            )
            assert first.source_links == expected_source_links
            assert db.scalar(
                select(func.count()).select_from(Source).where(Source.chapter_id.is_not(None))
            ) == sum(len(item.source_ids) for item in dataset.chapters)
            assert db.scalar(
                select(func.count()).select_from(Source).where(Source.faction_id.is_not(None))
            ) == sum(len(item.source_ids) for item in dataset.factions)

            chapter_source = db.scalar(
                select(Source).where(Source.chapter_id.is_not(None)).limit(1)
            )
            assert chapter_source is not None
            assert (
                get_source_by_id_published(
                    db,
                    chapter_source.id,
                    context=context_for(ProgressKey.START),
                )
                is None
            )
            assert (
                get_source_by_id_published(
                    db,
                    chapter_source.id,
                    context=context_for(ProgressKey.QINGHE),
                )
                is not None
            )
            current_faction_source = db.scalar(
                select(Source)
                .join(Faction, Source.faction_id == Faction.id)
                .join(Chapter, Faction.visible_after_chapter_id == Chapter.id)
                .where(Source.faction_id.is_not(None))
                .where(Chapter.progress_rank > 10)
                .limit(1)
            )
            assert current_faction_source is not None
            assert (
                get_source_by_id_published(
                    db,
                    current_faction_source.id,
                    context=context_for(ProgressKey.QINGHE),
                )
                is None
            )

            start_graph = get_graph(db=db, progress=ProgressKey.START)
            qinghe_graph = get_graph(db=db, progress=ProgressKey.QINGHE)
            assert start_graph.data is not None
            assert qinghe_graph.data is not None
            assert {node.slug for node in start_graph.data.nodes} == {
                item.slug
                for item in dataset.characters
                if item.visible_after_progress is ProgressKey.START and item.spoiler_level == 0
            }
            assert {node.slug for node in qinghe_graph.data.nodes} == {
                item.slug
                for item in dataset.characters
                if item.visible_after_progress in {ProgressKey.START, ProgressKey.QINGHE}
            }

            protagonist_detail = character_detail(
                slug="protagonist",
                db=db,
                progress=ProgressKey.QINGHE,
                reveal=False,
            )
            assert isinstance(protagonist_detail.data, CharacterDetail)
            protagonist_item = next(
                item for item in dataset.characters if item.slug == "protagonist"
            )
            assert len(protagonist_detail.data.sources) == len(protagonist_item.source_ids)

            visible_edge = qinghe_graph.data.edges[0]
            relationship_result = relationship_detail(
                relationship_id=visible_edge.id,
                db=db,
                progress=ProgressKey.QINGHE,
                reveal=False,
            )
            assert isinstance(relationship_result.data, RelationshipDetail)
            relationship_item = next(
                item
                for item in dataset.relationships
                if stable_content_id("relationship", item.id) == visible_edge.id
            )
            assert len(relationship_result.data.sources) == len(relationship_item.source_ids)

            start_timeline = get_timeline(db=db, progress=ProgressKey.START)
            qinghe_timeline = get_timeline(db=db, progress=ProgressKey.QINGHE)
            assert start_timeline.data is not None
            assert qinghe_timeline.data is not None
            assert {event.slug for event in start_timeline.data.events} == {
                item.slug
                for item in dataset.events
                if item.visible_after_progress is ProgressKey.START and item.spoiler_level == 0
            }
            assert {event.slug for event in qinghe_timeline.data.events} == {
                item.slug
                for item in dataset.events
                if item.visible_after_progress in {ProgressKey.START, ProgressKey.QINGHE}
            }
            source_counts_by_event = {event.slug: len(event.source_ids) for event in dataset.events}
            assert all(
                len(event.sources) == source_counts_by_event[event.slug]
                for event in qinghe_timeline.data.events
            )
            assert db.scalar(select(func.count()).select_from(ContentImportRun)) >= 1

            start_arcs = list_story_arcs(db=db, progress=ProgressKey.START)
            assert start_arcs.data is not None
            assert len(start_arcs.data.arcs) == 1
            assert start_arcs.data.arcs[0].slug == "qinghe-main-journey"
            assert start_arcs.data.arcs[0].beat_count == 1
            assert start_arcs.data.arcs[0].estimated_minutes == 12

            start_arc = get_story_arc(
                slug="qinghe-main-journey",
                db=db,
                progress=ProgressKey.START,
            )
            assert start_arc.data is not None
            assert [beat.event.slug for beat in start_arc.data.beats] == ["prologue-attack"]
            assert all(not beat.historical_contexts for beat in start_arc.data.beats)

            qinghe_arc = get_story_arc(
                slug="qinghe-main-journey",
                db=db,
                progress=ProgressKey.QINGHE,
            )
            assert qinghe_arc.data is not None
            assert len(qinghe_arc.data.beats) == 10
            wangqing = next(
                beat for beat in qinghe_arc.data.beats if beat.event.slug == "wangqing-battle"
            )
            assert len(wangqing.historical_contexts) == sum(
                1
                for link in dataset.event_historical_links
                if link.event_id == "evt-wangqing-battle"
            )
            assert all(card.references for card in wangqing.historical_contexts)
            assert all(
                reference.url.startswith(("http://", "https://"))
                for card in wangqing.historical_contexts
                for reference in card.references
            )
            assert all(beat.event.sources for beat in qinghe_arc.data.beats)

            import_dataset(db, dataset, replace_existing=True)
            assert db.get(Chapter, sentinel_id) is None
            assert db.scalar(select(func.count()).select_from(StoryArc)) == 1
            assert db.scalar(select(func.count()).select_from(StoryArcBeat)) == 10
            assert db.scalar(select(func.count()).select_from(HistoricalContext)) == len(
                dataset.historical_contexts
            )
            assert db.scalar(select(func.count()).select_from(EventHistoricalLink)) == len(
                dataset.event_historical_links
            )
        finally:
            db.rollback()
