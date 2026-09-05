from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import models as _models  # noqa: F401


def _sync_database_url() -> str:
    """Convert async database URL to sync for Alembic migrations."""
    url = settings.database_url
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


def _alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", "app/database/migrations")
    config.set_main_option("sqlalchemy.url", _sync_database_url())
    config.set_main_option("prepend_sys_path", ".")
    return config


def run_migrations() -> None:
    """Run database migrations using a synchronous engine."""
    config = _alembic_config()
    sync_engine = create_engine(_sync_database_url())
    with sync_engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


async def init_db() -> None:
    run_migrations()

    from app.services.identity_service import seed_administrators

    await seed_administrators(settings.admin_ids)


async def init_db_for_test() -> None:
    """Initialize database for tests using create_all (faster for SQLite test isolation)."""
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    from app.services.identity_service import seed_administrators

    await seed_administrators(settings.admin_ids)