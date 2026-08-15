from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import File
from app.database.repositories import create_file
from app.services.file_extractor import FileData


async def save_file(
    session: AsyncSession,
    file_data: FileData,
    uploaded_by: int,
) -> File:
    return await create_file(
        session=session,
        telegram_file_id=file_data.telegram_file_id,
        file_type=file_data.file_type,
        file_name=file_data.file_name,
        uploaded_by=uploaded_by,
    )