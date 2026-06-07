import pytest

from app.domain import ProgressKey
from app.services.spoiler import context_for, is_visible


@pytest.mark.parametrize(
    ("progress", "required_rank", "spoiler_level", "expected"),
    [
        (ProgressKey.START, 0, 0, True),
        (ProgressKey.START, 10, 0, False),
        (ProgressKey.START, 0, 1, False),
        (ProgressKey.QINGHE, 10, 3, True),
        (ProgressKey.QINGHE, 20, 0, False),
        (ProgressKey.KAIFENG, 20, 3, True),
        (ProgressKey.CURRENT, 90, 3, True),
        (ProgressKey.UNRESTRICTED, 100, 3, True),
    ],
)
def test_spoiler_matrix(
    progress: ProgressKey,
    required_rank: int,
    spoiler_level: int,
    expected: bool,
) -> None:
    assert (
        is_visible(
            context=context_for(progress),
            required_progress_rank=required_rank,
            spoiler_level=spoiler_level,
        )
        is expected
    )
