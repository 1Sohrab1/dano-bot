import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.middlewares.rate_limit import (
    ADMIN_SCOPE,
    RATE_LIMIT_REPLY,
    USER_SCOPE,
    RateLimitMiddleware,
)
from app.router.admin import admins
from app.router.admin.content import content_admin
from app.router.user import users
from app.services import rate_limit_service
from app.services.rate_limit_service import InMemoryRateLimitStore


def _fresh_store() -> InMemoryRateLimitStore:
    return InMemoryRateLimitStore()


def test_allows_requests_within_limit() -> None:
    store = _fresh_store()

    results = [
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=1, limit=3, store=store
            )
        )
        for _ in range(3)
    ]

    assert results == [True, True, True]


def test_blocks_requests_exceeding_limit() -> None:
    store = _fresh_store()

    for _ in range(3):
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=1, limit=3, store=store
            )
        )

    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=1, limit=3, store=store
            )
        )
        is False
    )


def test_limits_are_isolated_between_users() -> None:
    store = _fresh_store()

    for _ in range(2):
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=11, limit=2, store=store
            )
        )

    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=11, limit=2, store=store
            )
        )
        is False
    )
    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=22, limit=2, store=store
            )
        )
        is True
    )


def test_limits_are_isolated_between_scopes() -> None:
    store = _fresh_store()

    for _ in range(2):
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=33, limit=2, store=store
            )
        )

    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=33, limit=2, store=store
            )
        )
        is False
    )
    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="admin", user_id=33, limit=2, store=store
            )
        )
        is True
    )


def test_window_expiry_resets_counter() -> None:
    store = _fresh_store()

    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=44, limit=1, store=store, now=1000.0
            )
        )
        is True
    )
    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=44, limit=1, store=store, now=1001.0
            )
        )
        is False
    )
    assert (
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=44, limit=1, store=store, now=1061.0
            )
        )
        is True
    )


def test_storage_failure_fails_open(caplog: pytest.LogCaptureFixture) -> None:
    class BrokenStore:
        async def increment(
            self, key: str, window_seconds: int, *, now: float | None = None
        ) -> int:
            raise RuntimeError("backend down")

    with caplog.at_level(logging.WARNING):
        allowed = asyncio.run(
            rate_limit_service.is_allowed(
                scope="user", user_id=55, limit=1, store=BrokenStore()  # type: ignore[arg-type]
            )
        )

    assert allowed is True
    assert "event=rate_limit_store_failed" in caplog.text


def test_exceeded_limit_logs_structured_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = _fresh_store()

    with caplog.at_level(logging.INFO):
        asyncio.run(
            rate_limit_service.is_allowed(
                scope="admin", user_id=66, limit=1, store=store
            )
        )
        allowed = asyncio.run(
            rate_limit_service.is_allowed(
                scope="admin", user_id=66, limit=1, store=store
            )
        )

    assert allowed is False
    assert "event=rate_limit_exceeded scope=admin user_id=66" in caplog.text


def _make_message(user_id: int | None) -> MagicMock:
    event = MagicMock(spec=Message)
    event.from_user = (
        SimpleNamespace(id=user_id) if user_id is not None else None
    )
    event.answer = AsyncMock()
    return event


def _make_callback_query(user_id: int | None) -> MagicMock:
    event = MagicMock(spec=CallbackQuery)
    event.from_user = (
        SimpleNamespace(id=user_id) if user_id is not None else None
    )
    event.answer = AsyncMock()
    return event


def test_middleware_passes_allowed_event_to_handler() -> None:
    middleware = RateLimitMiddleware(scope=USER_SCOPE)
    event = _make_message(user_id=101)
    handler = AsyncMock(return_value="handled")

    result = asyncio.run(middleware(handler, event, {}))

    assert result == "handled"
    handler.assert_awaited_once()
    event.answer.assert_not_awaited()


def test_middleware_blocks_message_and_replies(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_user_per_minute", 1)
    middleware = RateLimitMiddleware(scope=USER_SCOPE)
    event = _make_message(user_id=102)
    handler = AsyncMock(return_value="handled")

    assert asyncio.run(middleware(handler, event, {})) == "handled"
    assert asyncio.run(middleware(handler, event, {})) is None

    handler.assert_awaited_once()
    event.answer.assert_awaited_once_with(RATE_LIMIT_REPLY)


def test_middleware_blocks_callback_query_and_replies(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_admin_per_minute", 1)
    middleware = RateLimitMiddleware(scope=ADMIN_SCOPE)
    event = _make_callback_query(user_id=103)
    handler = AsyncMock(return_value="handled")

    assert asyncio.run(middleware(handler, event, {})) == "handled"
    assert asyncio.run(middleware(handler, event, {})) is None

    handler.assert_awaited_once()
    event.answer.assert_awaited_once_with(RATE_LIMIT_REPLY)


def test_middleware_passes_through_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    monkeypatch.setattr(
        rate_limit_service, "is_allowed", AsyncMock(return_value=False)
    )
    middleware = RateLimitMiddleware(scope=USER_SCOPE)
    event = _make_message(user_id=104)
    handler = AsyncMock(return_value="handled")

    assert asyncio.run(middleware(handler, event, {})) == "handled"

    handler.assert_awaited_once()
    event.answer.assert_not_awaited()


def test_middleware_passes_event_without_user() -> None:
    middleware = RateLimitMiddleware(scope=USER_SCOPE)
    event = _make_message(user_id=None)
    handler = AsyncMock(return_value="handled")

    assert asyncio.run(middleware(handler, event, {})) == "handled"

    handler.assert_awaited_once()


def test_middleware_still_blocks_when_reply_fails(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_user_per_minute", 1)
    middleware = RateLimitMiddleware(scope=USER_SCOPE)
    event = _make_message(user_id=105)
    event.answer = AsyncMock(
        side_effect=TelegramAPIError(method="sendMessage", message="boom")
    )
    handler = AsyncMock(return_value="handled")

    assert asyncio.run(middleware(handler, event, {})) == "handled"
    assert asyncio.run(middleware(handler, event, {})) is None

    handler.assert_awaited_once()


def test_middleware_admin_scope_uses_admin_limit(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_user_per_minute", 1)
    monkeypatch.setattr(settings, "rate_limit_admin_per_minute", 100)
    middleware = RateLimitMiddleware(scope=ADMIN_SCOPE)
    handler = AsyncMock(return_value="handled")

    for _ in range(3):
        event = _make_message(user_id=106)
        assert asyncio.run(middleware(handler, event, {})) == "handled"

    assert handler.await_count == 3


def test_rate_limit_middleware_registered_on_routers() -> None:
    user_scopes = [
        middleware.scope
        for middleware in users.message.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]
    admin_scopes = [
        middleware.scope
        for middleware in admins.message.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]
    content_message_scopes = [
        middleware.scope
        for middleware in content_admin.message.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]
    content_callback_scopes = [
        middleware.scope
        for middleware in content_admin.callback_query.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]

    assert user_scopes == [USER_SCOPE]
    assert admin_scopes == [ADMIN_SCOPE]
    assert content_message_scopes == [ADMIN_SCOPE]
    assert content_callback_scopes == [ADMIN_SCOPE]
