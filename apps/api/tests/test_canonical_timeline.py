"""Phase D gate tests for the canonical-first timeline endpoint (D-G1..G6)."""

import os
from pathlib import Path

import pytest

from app.api.contracts import TimelineCanonicalData
from app.api.routes.timeline import get_timeline_canonical
from app.content_import import (
    import_canonical_dataset,
    import_dataset,
    load_canonical_dataset,
    load_dataset,
)
from app.db import SessionLocal
from app.domain import ProgressKey

DB_TEST = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)

V5_PATH = Path(__file__).parents[3] / "content" / "yysls-qinghe-v5.json"
CANONICAL_PATH = (
    Path(__file__).parents[3] / "content" / "yysls-qinghe-canonical-v0.1.json"
)


def _seed(db) -> None:
    import_dataset(db, load_dataset(V5_PATH))
    db.flush()
    import_canonical_dataset(
        db, load_canonical_dataset(CANONICAL_PATH), replace_existing=True
    )
    db.flush()


@DB_TEST
def test_canonical_spine_order_and_content() -> None:
    with SessionLocal() as db:
        try:
            _seed(db)
            data = get_timeline_canonical(db, progress=ProgressKey.QINGHE).data
            assert isinstance(data, TimelineCanonicalData)
            assert data.chapter_unlocked is True
            assert data.chapter is not None and data.chapter.slug == "qinghe"
            assert len(data.spine) == 18

            # D-G1: spine order is depth-first canonical order, starting at the chapter
            assert data.spine[0].canonical_key == "wwm:qinghe:chapter-1"
            assert data.spine[0].node_type.value == "chapter"
            assert data.spine[1].canonical_key == "wwm:qinghe:chapter-1:part-1"
            assert data.spine[2].canonical_key.endswith("part-1:awaken")

            # D-G4: zero-link canonical node is still present without interpretation
            break_temple = next(
                node
                for node in data.spine
                if node.canonical_key.endswith("part-2:break-temple")
            )
            assert break_temple.events == []

            # editorial-only event is NOT on the spine
            spine_slugs = {
                event.slug for node in data.spine for event in node.events
            }
            assert "wangqing-battle" not in spine_slugs
            assert "wangqing-battle" in {event.slug for event in data.unplaced_events}

            # D-G6: beat_index maps merged event to both nodes
            assert set(data.beat_index["p2-reunion"]) == {
                "wwm:qinghe:chapter-1:part-2:reunion",
                "wwm:qinghe:chapter-1:part-2:cisheng",
            }
        finally:
            db.rollback()


@DB_TEST
def test_canonical_locked_at_start_no_title_leak() -> None:
    """D-G5: at START the chapter spine is locked and no node titles leak."""
    with SessionLocal() as db:
        try:
            _seed(db)
            data = get_timeline_canonical(db, progress=ProgressKey.START).data
            assert isinstance(data, TimelineCanonicalData)
            assert data.chapter_unlocked is False
            assert data.spine == []
            assert data.chapter is not None and data.chapter.title == "第一章·神仙不渡"
        finally:
            db.rollback()


@DB_TEST
def test_canonical_unplaced_editorial_overlay_parity() -> None:
    """H-D1: editorial-only deep links keep full overlay parity.

    wangqing-battle has zero canonical links but must still load beat,
    sources, historical contexts, relationships and characters through the
    unplaced fallback (beat + history are the Story->History core sample).
    """
    with SessionLocal() as db:
        try:
            _seed(db)
            data = get_timeline_canonical(db, progress=ProgressKey.QINGHE).data
            wangqing = next(
                event for event in data.unplaced_events if event.slug == "wangqing-battle"
            )
            assert wangqing.beat is not None
            assert wangqing.beat.why_it_matters
            assert wangqing.sources
            assert wangqing.historical_contexts
            assert wangqing.relationships
            assert wangqing.characters
        finally:
            db.rollback()


@DB_TEST
def test_canonical_overlay_attaches_interpretation() -> None:
    """D-G3: StoryEvent + beat interpretation ride on the node without reordering."""
    with SessionLocal() as db:
        try:
            _seed(db)
            data = get_timeline_canonical(db, progress=ProgressKey.UNRESTRICTED).data
            arena = next(
                node
                for node in data.spine
                if node.canonical_key.endswith("part-1:arena")
            )
            assert len(arena.events) == 1
            event = arena.events[0]
            assert event.slug == "p1-arena"
            assert event.mapping_kind is not None and event.mapping_kind.value == "exact"
            assert len(event.characters) > 0
            assert event.beat is not None and event.beat.guide
        finally:
            db.rollback()
