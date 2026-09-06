import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage

from app.database.repositories import create_content
from app.router.user import handlers
from app.router.user.handlers import (
    CONTENT_EXPIRED_REPLY,
    CONTENT_INACTIVE_REPLY,
    CONTENT_NOT_FOUND_REPLY,
    DELIVERY_ERROR_REPLY,
    MEMBERSHIP_REQUIRED_REPLY,
    UNSUPPORTED_CODE_REPLY,
    content_deep_link_handler,
    start_handler,
)
from app.services.access_service import (
    ContentExpiredError,
    ContentInactiveError,
    ContentNotFoundError,
    DeliveryError,
    InvalidContentCodeError,
    MembershipRequiredError,
)


def _make_message(bot: object, from_user_id: int) -> tuple[SimpleNamespace, dict[str, str]]:
    recorded: dict[str, str] = {}

    async def answer(text: str, reply_markup=None) -> None:
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=from_user_id),
        bot=bot,
        answer=answer,
    )
    return message, recorded


def test_plain_start_behavior_is_unchanged() -> None:
    async def run() -> None:
        recorded: dict = {}

        async def answer(text: str, reply_markup=None) -> None:
            recorded["text"] = text
            recorded["reply_markup"] = reply_markup

        message = SimpleNamespace(
            from_user=SimpleNamespace(id=555),
            answer=answer,
        )
        await start_handler(message)
        assert "دانو" in recorded["text"]
        assert recorded["reply_markup"] is not None

    asyncio.run(run())


def test_deep_link_delivers_on_valid_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        bot = SimpleNamespace()
        message, recorded = _make_message(bot, from_user_id=777)
        delivery = AsyncMock(return_value=None)
        monkeypatch.setattr(handlers, "deliver_content", delivery)

        await content_deep_link_handler(
            message,
            SimpleNamespace(args="code1234"),
        )

        delivery.assert_awaited_once_with(
            bot,
            code="code1234",
            user_id=777,
        )
        assert "text" not in recorded

    asyncio.run(run())


def test_deep_link_persists_requesting_user(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run() -> None:
        bot = SimpleNamespace()
        message, _ = _make_message(bot, from_user_id=888)
        monkeypatch.setattr(handlers, "deliver_content", AsyncMock(return_value=None))

        await content_deep_link_handler(
            message,
            SimpleNamespace(args="code1234"),
        )

        from app.database.repositories import get_user_by_telegram_id

        user = await get_user_by_telegram_id(888)
        assert user is not None
        assert user.telegram_id == 888

    asyncio.run(run())


@pytest.mark.parametrize(
    ("exception", "expected_reply"),
    [
        (InvalidContentCodeError, UNSUPPORTED_CODE_REPLY),
        (ContentNotFoundError, CONTENT_NOT_FOUND_REPLY),
        (ContentInactiveError, CONTENT_INACTIVE_REPLY),
        (ContentExpiredError, CONTENT_EXPIRED_REPLY),
        (MembershipRequiredError, MEMBERSHIP_REQUIRED_REPLY),
        (DeliveryError, DELIVERY_ERROR_REPLY),
    ],
)
def test_deep_link_maps_domain_errors_to_safe_messages(
    exception: type[Exception],
    expected_reply: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        bot = SimpleNamespace()
        message, recorded = _make_message(bot, from_user_id=777)
        monkeypatch.setattr(
            handlers,
            "deliver_content",
            AsyncMock(side_effect=exception("code")),
        )

        await content_deep_link_handler(
            message,
            SimpleNamespace(args="badcode123"),
        )

        assert recorded["text"] == expected_reply
        assert "code" not in recorded["text"]

    asyncio.run(run())


def test_deep_link_end_to_end_delivers_stored_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        content = await create_content(
            source_chat_id=123,
            source_message_id=456,
            content_type="document",
            code="e2ecode001",
        )
        bot = AsyncMock()
        bot.copy_message.return_value = SimpleNamespace(message_id=1)
        message, recorded = _make_message(bot, from_user_id=999)

        from app.services import access_service

        monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

        await content_deep_link_handler(message, SimpleNamespace(args="e2ecode001"))

        bot.copy_message.assert_awaited_once_with(
            chat_id=999,
            from_chat_id=123,
            message_id=456,
        )
        assert "text" not in recorded
        assert content.code == "e2ecode001"

    asyncio.run(run())


def test_deep_link_telegram_failure_returns_generic_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        await create_content(
            source_chat_id=123,
            source_message_id=456,
            content_type="document",
            code="failcode01",
        )
        bot = AsyncMock()
        bot.copy_message.side_effect = TelegramAPIError(
            method=SendMessage(chat_id=1, text="x"),
            message="internal boom",
        )
        message, recorded = _make_message(bot, from_user_id=999)

        from app.services import access_service

        monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

        await content_deep_link_handler(message, SimpleNamespace(args="failcode01"))

        assert recorded["text"] == DELIVERY_ERROR_REPLY
        assert "boost" not in recorded["text"]
        assert "TelegramAPIError" not in recorded["text"]

    asyncio.run(run())