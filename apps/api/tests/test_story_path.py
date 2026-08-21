"""Regression fixtures for story_path parent-chain visibility (Wave 1 hardening)."""

import os
import uuid

import pytest

from app.api.contracts import CharacterDetail
from app.api.routes.details import character_detail
from app.db import SessionLocal
from app.domain import (
    ContentStatus,
    ProgressKey,
    StoryBeatRole,
)
from app.models import (
    Chapter,
    Character,
    StoryArc,
    StoryArcBeat,
    StoryEvent,
    event_characters,
)

pytestmark = [
    pytest.mark.skipif(
        os.getenv("RUN_DB_TESTS") != "1",
        reason="requires the local PostgreSQL test database",
    )
]


def test_story_path_requires_visible_parent_arc() -> None:
    """A published beat+event must not surface through an invisible parent arc.

    Fixture: character appears in a published spoiler-0 beat+event whose parent
    arc is DRAFT. story_path must stay empty until the arc becomes PUBLISHED.
    """
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            chapter = Chapter(
                id=uuid.uuid4(),
                slug=f"sp-chapter-{marker}",
                title="SP 章节",
                region=None,
                sort_order=9600,
                progress_key=ProgressKey.START,
                progress_rank=0,
                status=ContentStatus.PUBLISHED,
            )
            character = Character(
                id=uuid.uuid4(),
                slug=f"sp-character-{marker}",
                name="SP 测试人物",
                summary="用于父级闭包验证。",
                importance=1,
                spoiler_level=0,
                first_appear_chapter_id=chapter.id,
                status=ContentStatus.PUBLISHED,
            )
            event = StoryEvent(
                slug=f"sp-event-{marker}",
                title="SP 事件",
                summary="已发布事件。",
                chapter_id=chapter.id,
                sort_order=910,
                spoiler_level=0,
                status=ContentStatus.PUBLISHED,
            )
            db.add_all([chapter, character, event])
            db.flush()

            hidden_arc = StoryArc(
                slug=f"sp-arc-draft-{marker}",
                title="SP 未发布卷",
                summary="draft arc must not leak.",
                core_question="?",
                estimated_minutes=1,
                spoiler_level=0,
                status=ContentStatus.DRAFT,
            )
            db.add(hidden_arc)
            db.flush()
            draft_beat = StoryArcBeat(
                arc_id=hidden_arc.id,
                event_id=event.id,
                sort_order=1,
                role=StoryBeatRole.SETUP,
                guide="g",
                why_it_matters="w",
                bridge="b",
                next_question="n",
                spoiler_level=0,
                status=ContentStatus.PUBLISHED,
            )
            db.add(draft_beat)
            db.execute(
                event_characters.insert().values(
                    event_id=event.id, character_id=character.id
                )
            )
            db.flush()

            before = character_detail(
                slug=character.slug, db=db, progress=ProgressKey.START
            )
            assert isinstance(before.data, CharacterDetail)
            assert before.data.story_path == []

            hidden_arc.status = ContentStatus.PUBLISHED
            db.flush()

            after = character_detail(
                slug=character.slug, db=db, progress=ProgressKey.START
            )
            assert isinstance(after.data, CharacterDetail)
            assert len(after.data.story_path) == 1
            assert after.data.story_path[0].event_slug == event.slug
        finally:
            db.rollback()
