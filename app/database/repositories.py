from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database.database import engine
from app.database.models import Admin


async def is_admin(user_id: int) -> bool:
    async with AsyncSession(engine) as session:
        result = await session.exec(
            select(Admin).where(Admin.user_id == user_id)
        )
        return result.first() is not None