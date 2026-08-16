from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database.models import Admin

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
)


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    await initialize_admins()


async def initialize_admins() -> None:
    async with AsyncSession(engine) as session:
        result = await session.exec(select(Admin))
        existing_admins = result.all()

        if existing_admins:
            return

        for user_id in settings.admin_id_list:
            session.add(Admin(user_id=user_id))

        await session.commit()
