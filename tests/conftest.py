import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

_db_path = Path(os.environ.get("TMPDIR", "/tmp")) / "dano-bot-pytest.db"

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_IDS", "[123456789]")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_db_path.as_posix()}")
os.environ.setdefault("REQUIRED_CHANNEL_ID", "@test-channel")


@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    from sqlmodel import SQLModel

    from app.database.database import engine, init_db_for_test

    async def reset() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.drop_all)
        await init_db_for_test()

    asyncio.run(reset())
    yield
