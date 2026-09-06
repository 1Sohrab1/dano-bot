from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class UserFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None


class UserCallbackQueryFilter(BaseFilter):
    async def __call__(self, query: CallbackQuery) -> bool:
        return query.from_user is not None
