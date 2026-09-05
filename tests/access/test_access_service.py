import asyncio
import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage

from app.database.repositories import (
    create_content,
    deactivate_content,
    get_content_by_code,
)
from app.services import access_service
from app.services.access_service import (
    ContentExpiredError,
    ContentInactiveError,
    ContentNotFoundError,
    DeliveryError,
    InvalidContentCodeError,
    MembershipRequiredError,
    deliver_content,
)


def _make_content(
    *,
    code: str = "activecode01",
    expires_at: datetime | None = None,
) -> None:
    asyncio.run(
        create_content(
            source_chat_id=111,
            source_message_id=222,
            content_type="document",
            code=code,
            expires_at=expires_at,
        )
    )


def _fake_bot() -> AsyncMock:
    bot = AsyncMock()
    bot.copy_message.return_value = SimpleNamespace(message_id=1)
    return bot


def test_deliver_content_rejects_malformed_code(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bot = _fake_bot()
    get_mock = AsyncMock()
    monkeypatch.setattr(access_service, "get_content_by_code", get_mock)

    with caplog.at_level(logging.INFO), pytest.raises(InvalidContentCodeError):
        asyncio.run(deliver_content(bot, code="bad code!", user_id=10))

    get_mock.assert_not_awaited()
    bot.copy_message.assert_not_awaited()
    assert "event=access_denied reason=malformed user_id=10" in caplog.text


def test_deliver_content_rejects_unknown_code(
    caplog: pytest.LogCaptureFixture,
) -> None:
    bot = _fake_bot()

    with caplog.at_level(logging.INFO), pytest.raises(ContentNotFoundError):
        asyncio.run(deliver_content(bot, code="missingcode01", user_id=10))

    bot.copy_message.assert_not_awaited()
    assert "event=access_denied reason=not_found user_id=10" in caplog.text


def test_deliver_content_rejects_inactive_content(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _make_content(code="inactivecode1")
    asyncio.run(deactivate_content("inactivecode1"))
    bot = _fake_bot()
    monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

    with caplog.at_level(logging.INFO), pytest.raises(ContentInactiveError):
        asyncio.run(deliver_content(bot, code="inactivecode1", user_id=10))

    bot.copy_message.assert_not_awaited()
    assert "event=access_denied reason=inactive user_id=10" in caplog.text


def test_deliver_content_rejects_expired_content(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _make_content(
        code="expiredcode1",
        expires_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    bot = _fake_bot()
    monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

    with caplog.at_level(logging.INFO), pytest.raises(ContentExpiredError):
        asyncio.run(deliver_content(bot, code="expiredcode1", user_id=10))

    bot.copy_message.assert_not_awaited()
    assert "event=access_denied reason=expired user_id=10" in caplog.text


def test_deliver_content_requires_membership_and_skips_copy(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _make_content(code="membership01")
    bot = _fake_bot()
    monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=False))

    with caplog.at_level(logging.INFO), pytest.raises(MembershipRequiredError):
        asyncio.run(deliver_content(bot, code="membership01", user_id=10))

    bot.copy_message.assert_not_awaited()
    assert "event=access_denied reason=not_member user_id=10" in caplog.text
    access_service.is_member.assert_awaited_once_with(bot, user_id=10)


def test_deliver_content_copies_exact_stored_source_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _make_content(code="deliverable1")
    stored = asyncio.run(get_content_by_code("deliverable1"))
    bot = _fake_bot()
    monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

    with caplog.at_level(logging.INFO):
        asyncio.run(deliver_content(bot, code="deliverable1", user_id=10))

    assert stored is not None
    bot.copy_message.assert_awaited_once_with(
        chat_id=10,
        from_chat_id=stored.source_chat_id,
        message_id=stored.source_message_id,
    )
    assert f"event=delivery_success user_id=10 code=deliverable1 content_id={stored.id}" in caplog.text


def test_deliver_content_skips_membership_when_channel_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_content(code="nochannel01")
    bot = _fake_bot()
    monkeypatch.setattr("app.config.settings.required_channel_id", None)

    asyncio.run(deliver_content(bot, code="nochannel01", user_id=10))

    bot.copy_message.assert_awaited_once()
    bot.get_chat_member.assert_not_awaited()


def test_deliver_content_handles_telegram_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _make_content(code="failurec001")
    bot = _fake_bot()
    error = TelegramAPIError(method=SendMessage(chat_id=1, text="x"), message="boom")
    bot.copy_message.side_effect = error
    monkeypatch.setattr(access_service, "is_member", AsyncMock(return_value=True))

    with caplog.at_level(logging.WARNING), pytest.raises(DeliveryError):
        asyncio.run(deliver_content(bot, code="failurec001", user_id=10))

    assert "event=delivery_failed user_id=10 code=failurec001" in caplog.text
    assert "error_type=TelegramAPIError" in caplog.text
    assert "boom" not in caplog.text
    assert "test-token" not in caplog.text