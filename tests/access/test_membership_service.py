import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage

from app.services import membership_service
from app.services.membership_service import is_member

REQUIRED_CHANNEL = "@test-channel"


def _bot_with_member(status: ChatMemberStatus, **extra: object) -> AsyncMock:
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(status=status, **extra)
    return bot


def test_is_member_accepts_creator() -> None:
    bot = _bot_with_member(ChatMemberStatus.CREATOR)

    assert asyncio.run(is_member(bot, user_id=1)) is True
    bot.get_chat_member.assert_awaited_once_with(
        chat_id=REQUIRED_CHANNEL,
        user_id=1,
    )


def test_is_member_accepts_administrator() -> None:
    bot = _bot_with_member(ChatMemberStatus.ADMINISTRATOR)

    assert asyncio.run(is_member(bot, user_id=1)) is True


def test_is_member_accepts_member() -> None:
    bot = _bot_with_member(ChatMemberStatus.MEMBER)

    assert asyncio.run(is_member(bot, user_id=1)) is True


def test_is_member_accepts_restricted_member() -> None:
    bot = _bot_with_member(ChatMemberStatus.RESTRICTED, is_member=True)

    assert asyncio.run(is_member(bot, user_id=1)) is True


def test_is_member_rejects_restricted_non_member() -> None:
    bot = _bot_with_member(ChatMemberStatus.RESTRICTED, is_member=False)

    assert asyncio.run(is_member(bot, user_id=1)) is False


def test_is_member_rejects_left() -> None:
    bot = _bot_with_member(ChatMemberStatus.LEFT)

    assert asyncio.run(is_member(bot, user_id=1)) is False


def test_is_member_rejects_kicked() -> None:
    bot = _bot_with_member(ChatMemberStatus.KICKED)

    assert asyncio.run(is_member(bot, user_id=1)) is False


def test_is_member_skips_check_when_channel_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(membership_service.settings, "required_channel_id", None)
    bot = _bot_with_member(ChatMemberStatus.KICKED)

    assert asyncio.run(is_member(bot, user_id=1)) is True
    bot.get_chat_member.assert_not_awaited()


def test_is_member_skips_check_when_channel_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(membership_service.settings, "required_channel_id", "  ")
    bot = _bot_with_member(ChatMemberStatus.KICKED)

    assert asyncio.run(is_member(bot, user_id=1)) is True
    bot.get_chat_member.assert_not_awaited()


def test_is_member_fails_closed_on_telegram_error(caplog: pytest.LogCaptureFixture) -> None:
    error = TelegramAPIError(method=SendMessage(chat_id=1, text="x"), message="boom")
    bot = AsyncMock()
    bot.get_chat_member.side_effect = error

    with caplog.at_level(logging.WARNING):
        assert asyncio.run(is_member(bot, user_id=1)) is False

    assert "event=membership_check_failed" in caplog.text
    assert "user_id=1" in caplog.text