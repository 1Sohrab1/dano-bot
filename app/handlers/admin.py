from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.filters.admin import AdminFilter


router = Router(name="admin")

router.message.filter(AdminFilter())


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer("✅ شما ادمین هستید.")
