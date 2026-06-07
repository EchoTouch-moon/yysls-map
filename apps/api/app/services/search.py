from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.contracts import SearchResult
from app.domain import ContentStatus, ProgressKey
from app.models import Chapter, Character, Faction, StoryEvent
from app.services.spoiler import context_for, is_visible


@dataclass(frozen=True)
class RankedItem:
    result: SearchResult
    required_chapter_id: object | None
    spoiler_level: int


def _score(column: object, query: str):
    return func.greatest(func.similarity(column, query), 0.1)


def search_visible_content(
    db: Session,
    *,
    query: str,
    progress: ProgressKey,
    limit: int = 30,
) -> list[SearchResult]:
    normalized = query.strip()
    if not normalized:
        return []

    candidates: list[RankedItem] = []
    character_score = _score(Character.name, normalized)
    for character, score in db.execute(
        select(Character, character_score.label("score"))
        .where(
            Character.status == ContentStatus.PUBLISHED,
            or_(
                Character.name.ilike(f"%{normalized}%"),
                Character.summary.ilike(f"%{normalized}%"),
                func.similarity(Character.name, normalized) > 0.15,
            ),
        )
        .order_by(character_score.desc())
        .limit(limit)
    ):
        candidates.append(
            RankedItem(
                result=SearchResult(
                    kind="character",
                    slug=character.slug,
                    title=character.name,
                    summary=character.summary,
                    score=float(score),
                ),
                required_chapter_id=(
                    character.visible_after_chapter_id or character.first_appear_chapter_id
                ),
                spoiler_level=character.spoiler_level,
            )
        )

    faction_score = _score(Faction.name, normalized)
    for faction, score in db.execute(
        select(Faction, faction_score.label("score"))
        .where(
            Faction.status == ContentStatus.PUBLISHED,
            or_(
                Faction.name.ilike(f"%{normalized}%"),
                Faction.summary.ilike(f"%{normalized}%"),
                func.similarity(Faction.name, normalized) > 0.15,
            ),
        )
        .order_by(faction_score.desc())
        .limit(limit)
    ):
        candidates.append(
            RankedItem(
                result=SearchResult(
                    kind="faction",
                    slug=faction.slug,
                    title=faction.name,
                    summary=faction.summary,
                    score=float(score),
                ),
                required_chapter_id=faction.visible_after_chapter_id,
                spoiler_level=faction.spoiler_level,
            )
        )

    event_score = _score(StoryEvent.title, normalized)
    for event, score in db.execute(
        select(StoryEvent, event_score.label("score"))
        .where(
            StoryEvent.status == ContentStatus.PUBLISHED,
            or_(
                StoryEvent.title.ilike(f"%{normalized}%"),
                StoryEvent.summary.ilike(f"%{normalized}%"),
                func.similarity(StoryEvent.title, normalized) > 0.15,
            ),
        )
        .order_by(event_score.desc())
        .limit(limit)
    ):
        candidates.append(
            RankedItem(
                result=SearchResult(
                    kind="event",
                    slug=event.slug,
                    title=event.title,
                    summary=event.summary,
                    score=float(score),
                ),
                required_chapter_id=event.visible_after_chapter_id or event.chapter_id,
                spoiler_level=event.spoiler_level,
            )
        )

    ranks = {
        chapter_id: rank
        for chapter_id, rank in db.execute(select(Chapter.id, Chapter.progress_rank)).all()
    }
    context = context_for(progress)
    results = [
        candidate.result
        for candidate in candidates
        if is_visible(
            context=context,
            required_progress_rank=ranks.get(candidate.required_chapter_id),
            spoiler_level=candidate.spoiler_level,
        )
    ]
    return sorted(results, key=lambda item: (-item.score, item.kind, item.slug))[:limit]

