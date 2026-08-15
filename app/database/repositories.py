from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database.models import File


async def create_file(
    session: AsyncSession,
    telegram_file_id: str,
    file_type: str,
    file_name: str | None,
    uploaded_by: int,
) -> File:
    file = File(
        telegram_file_id=telegram_file_id,
        file_type=file_type,
        file_name=file_name,
        uploaded_by=uploaded_by,
    )

    session.add(file)
    await session.commit()
    await session.refresh(file)

    return file


async def get_file_by_id(
    session: AsyncSession,
    file_id: int,
) -> File | None:
    result = await session.execute(
        select(File).where(File.id == file_id)
    )

    return result.scalar_one_or_none()