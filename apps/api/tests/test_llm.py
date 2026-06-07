import pytest
from fastapi import HTTPException

from app.services.llm import AnthropicCompatibleExtractor


def test_llm_disabled_by_default() -> None:
    with pytest.raises(HTTPException) as exc_info:
        AnthropicCompatibleExtractor()
    assert exc_info.value.status_code == 503

