import asyncio
import logging
from datetime import UTC, datetime, timedelta

import pytest

from app.database.models import ContentState
from app.database.repositories import (
    create_content,
    get_content_by_code,
)
from app.services.content_management_service import (
    CONTENT_PAGE_SIZE,
    ContentAlreadyActiveError,
    ContentAlreadyInactiveError,
    ContentNotFoundError,
    InvalidContentCodeError,
    InvalidExpirationValueError,
    activate_content,
    deactivate_content,
    delete_content,
    list_content,
    preview_content,
    set_content_expiration,
)


def _seed(
    *codes: str,
    state: str = ContentState.ACTIVE,
    expires_at: datetime | None = None,
) -> None:
    for code in codes:
        asyncio.run(
            create_content(
                source_chat_id=123,
                source_message_id=456,
                content_type="document",
                code=code,
                state=state,
                expires_at=expires_at,
            )
        )


def test_list_content_is_bounded_and_ordered() -> None:
    _seed(*[f"code{i:03d}" for i in range(25)])

    page1 = asyncio.run(list_content(1))
    page2 = asyncio.run(list_content(2))
    page3 = asyncio.run(list_content(3))

    assert page1.page == 1
    assert page2.page == 2
    assert page3.page == 3
    assert page1.total == 25
    assert page1.total_pages == 3
    assert page1.page_size == CONTENT_PAGE_SIZE == 10
    assert len(page1.items) == 10
    assert len(page2.items) == 10
    assert len(page3.items) == 5

    ids = (
        [item.id for item in page1.items]
        + [item.id for item in page2.items]
        + [item.id for item in page3.items]
    )
    assert ids == sorted(ids, reverse=True)
    assert len(set(ids)) == 25


def test_list_content_is_stable_across_calls() -> None:
    _seed(*[f"stable{i:02d}" for i in range(10)])

    first = asyncio.run(list_content(1))
    second = asyncio.run(list_content(1))

    assert [item.id for item in first.items] == [item.id for item in second.items]


def test_list_content_clamps_page_above_last() -> None:
    _seed("clamp0001", "clamp0002", "clamp0003", "clamp0004", "clamp0005")

    result = asyncio.run(list_content(99))

    assert result.page == 1
    assert result.total_pages == 1
    assert len(result.items) == 5


def test_list_content_clamps_page_below_first() -> None:
    _seed("clamp0001")

    result = asyncio.run(list_content(0))

    assert result.page == 1
    assert len(result.items) == 1


def test_list_content_handles_empty_store() -> None:
    result = asyncio.run(list_content(5))

    assert result.page == 1
    assert result.total == 0
    assert result.total_pages == 1
    assert result.items == []


def test_preview_content_resolves_existing_content() -> None:
    _seed("preview001")

    content = asyncio.run(preview_content("preview001"))

    assert content is not None
    assert content.code == "preview001"


def test_preview_content_rejects_unknown_code() -> None:
    with pytest.raises(ContentNotFoundError):
        asyncio.run(preview_content("nonexist01"))


def test_activate_content_flips_inactive_to_active() -> None:
    _seed("activate01", state=ContentState.INACTIVE)

    updated = asyncio.run(activate_content("activate01", actor=111))

    assert updated.state == ContentState.ACTIVE
    assert asyncio.run(get_content_by_code("activate01")).state == ContentState.ACTIVE


def test_activate_content_rejects_already_active() -> None:
    _seed("activate02")

    with pytest.raises(ContentAlreadyActiveError):
        asyncio.run(activate_content("activate02", actor=111))


def test_deactivate_content_flips_active_to_inactive() -> None:
    _seed("deactivat1")

    updated = asyncio.run(deactivate_content("deactivat1", actor=111))

    assert updated.state == ContentState.INACTIVE
    assert asyncio.run(get_content_by_code("deactivat1")).state == ContentState.INACTIVE


def test_deactivate_content_rejects_already_inactive() -> None:
    _seed("deactivat2", state=ContentState.INACTIVE)

    with pytest.raises(ContentAlreadyInactiveError):
        asyncio.run(deactivate_content("deactivat2", actor=111))


def test_delete_content_removes_row() -> None:
    _seed("deletecode1")

    deleted = asyncio.run(delete_content("deletecode1", actor=111))

    assert deleted.code == "deletecode1"
    assert asyncio.run(get_content_by_code("deletecode1")) is None


def test_mutations_reject_unknown_code() -> None:
    with pytest.raises(ContentNotFoundError):
        asyncio.run(activate_content("nonexist01", actor=111))
    with pytest.raises(ContentNotFoundError):
        asyncio.run(deactivate_content("nonexist01", actor=111))
    with pytest.raises(ContentNotFoundError):
        asyncio.run(delete_content("nonexist01", actor=111))
    with pytest.raises(ContentNotFoundError):
        asyncio.run(set_content_expiration("nonexist01", 7, actor=111))


def test_mutations_reject_malformed_code() -> None:
    with pytest.raises(InvalidContentCodeError):
        asyncio.run(activate_content("bad code", actor=111))
    with pytest.raises(InvalidContentCodeError):
        asyncio.run(delete_content("bad code", actor=111))
    with pytest.raises(InvalidContentCodeError):
        asyncio.run(set_content_expiration("bad code", 7, actor=111))


def test_set_content_expiration_sets_relative_date() -> None:
    _seed("expirecode1")
    before = datetime.now(UTC)

    updated = asyncio.run(set_content_expiration("expirecode1", 7, actor=111))

    after = datetime.now(UTC)
    assert updated.expires_at is not None
    assert before + timedelta(days=7) <= updated.expires_at <= after + timedelta(days=7)

    stored = asyncio.run(get_content_by_code("expirecode1"))
    assert stored is not None
    assert stored.expires_at == updated.expires_at


def test_set_content_expiration_clears() -> None:
    _seed("expirecode2", expires_at=datetime(2030, 1, 1, tzinfo=UTC))

    updated = asyncio.run(set_content_expiration("expirecode2", None, actor=111))

    assert updated.expires_at is None
    stored = asyncio.run(get_content_by_code("expirecode2"))
    assert stored is not None
    assert stored.expires_at is None


def test_set_content_expiration_rejects_invalid_days() -> None:
    _seed("expirecode3")

    with pytest.raises(InvalidExpirationValueError):
        asyncio.run(set_content_expiration("expirecode3", 0, actor=111))
    with pytest.raises(InvalidExpirationValueError):
        asyncio.run(set_content_expiration("expirecode3", -1, actor=111))


def test_activate_logs_structured_event(caplog: pytest.LogCaptureFixture) -> None:
    _seed("loggedcode2", state=ContentState.INACTIVE)

    with caplog.at_level(logging.INFO):
        asyncio.run(activate_content("loggedcode2", actor=222))

    assert "event=content_activated actor=222 code=loggedcode2" in caplog.text


def test_delete_logs_structured_event(caplog: pytest.LogCaptureFixture) -> None:
    _seed("loggedcode1")

    with caplog.at_level(logging.INFO):
        asyncio.run(delete_content("loggedcode1", actor=111))

    assert "event=content_deleted actor=111 code=loggedcode1" in caplog.text


def test_expiration_logs_structured_event(caplog: pytest.LogCaptureFixture) -> None:
    _seed("loggedcode3")

    with caplog.at_level(logging.INFO):
        asyncio.run(set_content_expiration("loggedcode3", 3, actor=333))

    assert "event=content_expiration_set actor=333 code=loggedcode3" in caplog.text
    assert "days=3" in caplog.text