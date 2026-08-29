from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        return await handler(event, data)
