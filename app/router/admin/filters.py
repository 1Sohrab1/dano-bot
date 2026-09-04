from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config import settings


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False

        return message.from_user.id in settings.admin_id_list
