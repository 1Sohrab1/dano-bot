import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.database.database import init_db
# from app.routers.admin import router as admin_router


# dp = Dispatcher()

# dp.include_router(admin_router)


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "سلام 👋\n"
        "به دانو بات خوش اومدی 🤖"
    )


async def main() -> None:
    await init_db()

    bot = Bot(token=settings.bot_token)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())