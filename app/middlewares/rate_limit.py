import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.services import rate_limit_service

logger = logging.getLogger(__name__)

USER_SCOPE = "user"
ADMIN_SCOPE = "admin"

RATE_LIMIT_REPLY = "درخواست‌های شما بیش از حد مجاز است. لطفاً کمی بعد تلاش کنید."


class RateLimitMiddleware(BaseMiddleware):
    """Enforce per-user fixed-window rate limits for one router scope.

    The limit is resolved from `Settings` on every event so configuration
    changes apply without re-registering the middleware. Events that cannot
    be attributed to a user pass through; storage failures fail open.
    Blocked events never reach handlers.
    """

    def __init__(self, *, scope: str) -> None:
        self._scope = scope

    @property
    def scope(self) -> str:
        return self._scope

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not settings.rate_limit_enabled:
            return await handler(event, data)

        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return await handler(event, data)

        if self._scope == ADMIN_SCOPE:
            limit = settings.rate_limit_admin_per_minute
        else:
            limit = settings.rate_limit_user_per_minute

        allowed = await rate_limit_service.is_allowed(
            scope=self._scope,
            user_id=from_user.id,
            limit=limit,
        )
        if allowed:
            return await handler(event, data)

        try:
            if isinstance(event, (Message, CallbackQuery)):
                await event.answer(RATE_LIMIT_REPLY)
        except TelegramAPIError as error:
            logger.warning(
                "event=rate_limit_reply_failed scope=%s user_id=%s error_type=%s",
                self._scope,
                from_user.id,
                error.__class__.__name__,
            )
        return None
