from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.services.admin_service import is_admin


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False

        return await is_admin(message.from_user.id)


class AdminCallbackQueryFilter(BaseFilter):
    async def __call__(self, query: CallbackQuery) -> bool:
        if query.from_user is None:
            return False

        return await is_admin(query.from_user.id)
