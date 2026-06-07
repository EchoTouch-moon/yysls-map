import pytest

from app.seed import (
    CHAPTERS,
    CHARACTERS,
    EVENTS,
    FACTIONS,
    RELATIONSHIPS,
    SeedValidationError,
    validate_seed,
)


def test_demo_seed_definitions_are_valid() -> None:
    validate_seed()
    assert len(CHAPTERS) == 5
    assert len(FACTIONS) == 5
    assert len(CHARACTERS) == 20
    assert len(RELATIONSHIPS) == 30
    assert len(EVENTS) == 10


def test_seed_validator_rejects_duplicate_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.seed as seed_module

    monkeypatch.setattr(
        seed_module,
        "RELATIONSHIPS",
        (*RELATIONSHIPS, RELATIONSHIPS[0]),
    )
    with pytest.raises(SeedValidationError, match="duplicate relationship"):
        validate_seed()
