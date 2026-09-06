import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.router.user import handlers
from app.router.user.callbacks import MembershipCheck
from app.router.user.handlers import (
    CONTENT_INACTIVE_REPLY,
    CONTENT_NOT_FOUND_REPLY,
    MEMBERSHIP_PENDING_REPLY,
    MEMBERSHIP_REQUIRED_REPLY,
    MEMBERSHIP_RESOLVED_REPLY,
    content_deep_link_handler,
    membership_check_callback,
)
from app.router.user.keyboards import membership_keyboard
from app.services.access_service import (
    ContentInactiveError,
    MembershipRequiredError,
)


def _make_message(bot: object, from_user_id: int) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=from_user_id),
            bot=bot,
            answer=answer,
        ),
        recorded,
    )


def _make_query(bot: object, from_user_id: int = 555) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text=None, show_alert: bool = False):
        recorded["answer"] = text
        recorded["show_alert"] = show_alert

    async def edit_text(text, reply_markup=None):
        recorded["edit_text"] = text
        recorded["edit_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=from_user_id),
            message=SimpleNamespace(edit_text=edit_text),
            answer=answer,
        ),
        recorded,
    )


def test_membership_keyboard_builds_join_and_check_buttons() -> None:
    keyboard = membership_keyboard("code1234", "https://t.me/test-channel")

    rows = keyboard.inline_keyboard
    assert rows[0][0].text == "عضویت در کانال"
    assert rows[0][0].url == "https://t.me/test-channel"
    assert rows[1][0].text == "بررسی عضویت"
    unpacked = MembershipCheck.unpack(rows[1][0].callback_data)
    assert unpacked.code == "code1234"


def test_membership_keyboard_omits_join_button_without_channel() -> None:
    keyboard = membership_keyboard("code1234", None)

    rows = keyboard.inline_keyboard
    assert len(rows) == 1
    assert rows[0][0].text == "بررسی عضویت"


def test_membership_callback_data_round_trip() -> None:
    assert MembershipCheck.unpack(MembershipCheck(code="code1234").pack()).code == "code1234"


def test_deep_link_membership_required_shows_recovery_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = SimpleNamespace()
    message, recorded = _make_message(bot, from_user_id=777)
    monkeypatch.setattr(
        handlers,
        "deliver_content",
        AsyncMock(side_effect=MembershipRequiredError("code1234")),
    )

    asyncio.run(content_deep_link_handler(message, SimpleNamespace(args="code1234")))

    assert recorded["text"] == MEMBERSHIP_REQUIRED_REPLY
    assert recorded["reply_markup"] is not None
    rows = recorded["reply_markup"].inline_keyboard
    assert rows[0][0].text == "عضویت در کانال"
    assert rows[0][0].url == "https://t.me/test-channel"
    assert rows[1][0].text == "بررسی عضویت"
    unpacked = MembershipCheck.unpack(rows[1][0].callback_data)
    assert unpacked.code == "code1234"


def test_membership_retry_resumes_delivery_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = AsyncMock()
    query, recorded = _make_query(bot)
    delivery = AsyncMock(return_value=None)
    monkeypatch.setattr(handlers, "deliver_content", delivery)

    asyncio.run(
        membership_check_callback(
            query, MembershipCheck(code="code1234"), bot
        )
    )

    delivery.assert_awaited_once_with(bot, code="code1234", user_id=555)
    assert recorded["answer"] == MEMBERSHIP_RESOLVED_REPLY
    assert recorded["edit_text"] == MEMBERSHIP_RESOLVED_REPLY


def test_membership_retry_failure_keeps_recovery_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = AsyncMock()
    query, recorded = _make_query(bot)
    monkeypatch.setattr(
        handlers,
        "deliver_content",
        AsyncMock(side_effect=MembershipRequiredError("code1234")),
    )

    asyncio.run(
        membership_check_callback(
            query, MembershipCheck(code="code1234"), bot
        )
    )

    assert recorded["answer"] == MEMBERSHIP_PENDING_REPLY
    assert "edit_text" not in recorded


def test_membership_retry_non_membership_error_clears_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = AsyncMock()
    query, recorded = _make_query(bot)
    monkeypatch.setattr(
        handlers,
        "deliver_content",
        AsyncMock(side_effect=ContentInactiveError("code1234")),
    )

    asyncio.run(
        membership_check_callback(
            query, MembershipCheck(code="code1234"), bot
        )
    )

    assert recorded["answer"] == CONTENT_INACTIVE_REPLY
    assert recorded["edit_text"] == CONTENT_INACTIVE_REPLY


def test_membership_retry_not_found_maps_safe_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.access_service import ContentNotFoundError

    bot = AsyncMock()
    query, recorded = _make_query(bot)
    monkeypatch.setattr(
        handlers,
        "deliver_content",
        AsyncMock(side_effect=ContentNotFoundError("code1234")),
    )

    asyncio.run(
        membership_check_callback(
            query, MembershipCheck(code="code1234"), bot
        )
    )

    assert recorded["answer"] == CONTENT_NOT_FOUND_REPLY
    assert "code1234" not in recorded["edit_text"]


def test_deep_link_membership_prompt_uses_command_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = SimpleNamespace()
    message, recorded = _make_message(bot, from_user_id=777)
    monkeypatch.setattr(
        handlers,
        "deliver_content",
        AsyncMock(side_effect=MembershipRequiredError("deepcode01")),
    )

    asyncio.run(content_deep_link_handler(message, SimpleNamespace(args="deepcode01")))

    rows = recorded["reply_markup"].inline_keyboard
    unpacked = MembershipCheck.unpack(rows[1][0].callback_data)
    assert unpacked.code == "deepcode01"