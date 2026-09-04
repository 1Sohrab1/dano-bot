import re

from app.services.content_service import (
    CODE_ALPHABET,
    CODE_LENGTH,
    generate_content_code,
    is_deep_link_safe_code,
)


def test_generate_content_code_is_deep_link_safe() -> None:
    codes = {generate_content_code() for _ in range(50)}

    assert all(len(code) == CODE_LENGTH for code in codes)
    assert all(is_deep_link_safe_code(code) for code in codes)
    assert all(re.fullmatch(rf"[{re.escape(CODE_ALPHABET)}]+", code) for code in codes)
    assert len(codes) == 50


def test_is_deep_link_safe_code_rejects_invalid_characters() -> None:
    assert is_deep_link_safe_code("Ab12_-cdEF") is True
    assert is_deep_link_safe_code("bad code") is False
    assert is_deep_link_safe_code("equals=") is False
    assert is_deep_link_safe_code("") is False
