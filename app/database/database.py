from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
)


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)