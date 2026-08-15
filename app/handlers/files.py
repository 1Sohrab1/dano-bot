from aiogram import Router
from aiogram.types import Message

from app.database.database import async_session_factory
from app.services.admin_service import is_admin
from app.services.file_extractor import extract_file
from app.services.file_service import save_file


router = Router()


@router.message()
async def file_upload_handler(message: Message) -> None:
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        return

    file_data = extract_file(message)

    if file_data is None:
        return

    async with async_session_factory() as session:
        file = await save_file(
            session=session,
            file_data=file_data,
            uploaded_by=message.from_user.id,
        )

    await message.answer(
        f"✅ فایل ذخیره شد.\n"
        f"ID: `{file.id}`\n"
        f"نوع: `{file.file_type}`",
        parse_mode="Markdown",
    )