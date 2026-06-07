from dataclasses import dataclass
from typing import Protocol

from app.domain import PROGRESS_RANK, ProgressKey


class SpoilerSubject(Protocol):
    spoiler_level: int
    visible_after_chapter_id: object | None


@dataclass(frozen=True)
class SpoilerContext:
    progress: ProgressKey
    progress_rank: int
    allow_reveal: bool = False


def context_for(progress: ProgressKey, *, allow_reveal: bool = False) -> SpoilerContext:
    return SpoilerContext(
        progress=progress,
        progress_rank=PROGRESS_RANK[progress],
        allow_reveal=allow_reveal and progress is not ProgressKey.UNRESTRICTED,
    )


def is_visible(
    *,
    context: SpoilerContext,
    required_progress_rank: int | None,
    spoiler_level: int,
) -> bool:
    if context.progress is ProgressKey.UNRESTRICTED or context.allow_reveal:
        return True
    if required_progress_rank is not None and required_progress_rank > context.progress_rank:
        return False
    max_spoiler_level = 0 if context.progress is ProgressKey.START else 3
    return spoiler_level <= max_spoiler_level
