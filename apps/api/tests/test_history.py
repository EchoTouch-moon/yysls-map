"""Regression fixtures for history-card visibility closure (Wave 1 hardening)."""

import os
import uuid

import pytest
from fastapi import HTTPException

from app.api.contracts import HistoryDetailRead
from app.api.routes.history import get_history, list_history
from app.db import SessionLocal
from app.domain import (
    ContentStatus,
    HistoricalFactKind,
    HistoricalRelationKind,
    ProgressKey,
    StoryBeatRole,
)
from app.models import (
    Chapter,
    EventHistoricalLink,
    HistoricalContext,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
)
from app.schemas import RestrictedData

pytestmark = [
    pytest.mark.skipif(
        os.getenv("RUN_DB_TESTS") != "1",
        reason="requires the local PostgreSQL test database",
    )
]


def test_history_related_beats_visibility_closure() -> None:
    """A spoiler-safe card must not leak future narrative through related beats.

    Fixture: a spoiler-0 historical context linked to a future event/beat/arc
    chain that is invisible at START. At progress=START the card itself is
    readable, but `related` must be empty; at QINGHE the related beat appears.
    """
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            future_chapter = Chapter(
                id=uuid.uuid4(),
                slug=f"h1-future-{marker}",
                title="H1 未来章节",
                region=None,
                sort_order=9500,
                progress_key=ProgressKey.QINGHE,
                progress_rank=10,
                status=ContentStatus.PUBLISHED,
            )
            arc = StoryArc(
                slug=f"h1-arc-{marker}",
                title="H1 未公开卷",
                summary="用于可见性回归验证。",
                core_question="低进度读者是否会被泄露？",
                estimated_minutes=1,
                visible_after_chapter_id=future_chapter.id,
                spoiler_level=3,
                status=ContentStatus.PUBLISHED,
            )
            event = StoryEvent(
                slug=f"h1-event-{marker}",
                title="H1 未来事件",
                summary="尚未解锁的事件标题。",
                chapter_id=future_chapter.id,
                sort_order=900,
                spoiler_level=3,
                visible_after_chapter_id=future_chapter.id,
                status=ContentStatus.PUBLISHED,
            )
            safe_card = HistoricalContext(
                slug=f"hist-h1-safe-{marker}",
                title="H1 安全历史卡",
                period_label="无年代",
                summary="spoiler 0 的可核史实。",
                fact_kind=HistoricalFactKind.HISTORICAL_FACT,
                boundary_note="仅验证闭包。",
                spoiler_level=0,
                status=ContentStatus.PUBLISHED,
            )
            db.add_all([future_chapter, arc, event, safe_card])
            db.flush()

            beat = StoryArcBeat(
                arc_id=arc.id,
                event_id=event.id,
                sort_order=1,
                role=StoryBeatRole.SETUP,
                guide="guide",
                why_it_matters="why",
                bridge="bridge",
                next_question="next",
                visible_after_chapter_id=future_chapter.id,
                spoiler_level=3,
                status=ContentStatus.PUBLISHED,
            )
            link = EventHistoricalLink(
                event_id=event.id,
                context_id=safe_card.id,
                relation_kind=HistoricalRelationKind.SETTING,
                editorial_note="closure fixture",
                sort_order=1,
                visible_after_chapter_id=future_chapter.id,
                spoiler_level=3,
                status=ContentStatus.PUBLISHED,
            )
            db.add_all([beat, link])
            db.flush()

            at_start = get_history(slug=safe_card.slug, db=db, progress=ProgressKey.START)
            assert isinstance(at_start.data, HistoryDetailRead)
            assert at_start.data.boundary_note == "仅验证闭包。"
            # H1 closure: card is readable at START, but the future beat stays hidden.
            assert at_start.data.related == []

            start_list = list_history(db=db, progress=ProgressKey.START)
            assert start_list.data is not None
            assert any(item.slug == safe_card.slug for item in start_list.data.contexts)

            at_qinghe = get_history(slug=safe_card.slug, db=db, progress=ProgressKey.QINGHE)
            assert isinstance(at_qinghe.data, HistoryDetailRead)
            assert [item.event_slug for item in at_qinghe.data.related] == [event.slug]
        finally:
            db.rollback()


def test_get_history_unknown_slug_raises_404() -> None:
    with SessionLocal() as db:
        try:
            with pytest.raises(HTTPException) as exc_info:
                get_history(
                    slug=f"hist-h1-none-{uuid.uuid4().hex[:8]}",
                    db=db,
                    progress=ProgressKey.QINGHE,
                )
            assert exc_info.value.status_code == 404
        finally:
            db.rollback()


def test_get_history_restricted_below_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    """A high-spoiler card returns RestrictedData instead of its content."""
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            secret_card = HistoricalContext(
                slug=f"hist-h1-secret-{marker}",
                title="H1 受限历史卡",
                period_label="后晋开运三年（946）",
                summary="低进度不应看到的内容。",
                fact_kind=HistoricalFactKind.HISTORICAL_FACT,
                boundary_note="restricted fixture",
                spoiler_level=2,
                status=ContentStatus.PUBLISHED,
            )
            db.add(secret_card)
            db.flush()

            restricted = get_history(
                slug=secret_card.slug, db=db, progress=ProgressKey.START
            )
            assert isinstance(restricted.data, RestrictedData)
            assert restricted.data.required_progress in (None, "qinghe")
        finally:
            db.rollback()
