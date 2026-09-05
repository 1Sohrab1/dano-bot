import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _alembic_config(database_url: str) -> Config:
    """Create alembic config using the project's alembic.ini."""
    config = Config("alembic.ini")
    # Override the database URL
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _sync_engine_url(async_url: str) -> str:
    """Convert async URL to sync for inspection."""
    if async_url.startswith("sqlite+aiosqlite://"):
        return async_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return async_url


def test_migration_upgrade_creates_tables() -> None:
    """Test that migrations create all expected tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        database_url = f"sqlite+aiosqlite:///{db_path}"
        config = _alembic_config(database_url)
        sync_url = _sync_engine_url(database_url)

        # Run upgrade
        command.upgrade(config, "head")

        # Verify tables exist
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()

        expected_tables = {"user", "admin", "content", "alembic_version"}
        assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"

        # Verify content table columns
        with engine.connect() as conn:
            inspector = inspect(conn)
            content_columns = {col["name"] for col in inspector.get_columns("content")}
            expected_content_columns = {
                "id",
                "source_chat_id",
                "source_message_id",
                "content_type",
                "code",
                "state",
                "created_at",
                "expires_at",
            }
            assert expected_content_columns.issubset(content_columns)

            # Verify indexes
            content_indexes = {idx["name"] for idx in inspector.get_indexes("content")}
            assert "ix_content_code" in content_indexes
            assert "ix_content_state" in content_indexes

            # Verify user table
            user_columns = {col["name"] for col in inspector.get_columns("user")}
            assert {"id", "telegram_id"}.issubset(user_columns)

            # Verify admin table
            admin_columns = {col["name"] for col in inspector.get_columns("admin")}
            assert {"id", "telegram_id", "user_id"}.issubset(admin_columns)

            # Verify foreign key
            admin_fks = inspector.get_foreign_keys("admin")
            assert any(fk["referred_table"] == "user" for fk in admin_fks)

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_migration_downgrade_removes_tables() -> None:
    """Test that migrations can be downgraded cleanly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        database_url = f"sqlite+aiosqlite:///{db_path}"
        config = _alembic_config(database_url)
        sync_url = _sync_engine_url(database_url)

        # Upgrade then downgrade
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        # Verify tables are removed (except alembic_version)
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()

        assert "user" not in tables
        assert "admin" not in tables
        assert "content" not in tables
        # alembic_version may or may not exist after downgrade

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_migration_upgrade_downgrade_upgrade_cycle() -> None:
    """Test full migration cycle: upgrade -> downgrade -> upgrade."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        database_url = f"sqlite+aiosqlite:///{db_path}"
        config = _alembic_config(database_url)
        sync_url = _sync_engine_url(database_url)

        # First upgrade
        command.upgrade(config, "head")

        # Downgrade
        command.downgrade(config, "base")

        # Upgrade again
        command.upgrade(config, "head")

        # Verify tables exist
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()

        expected_tables = {"user", "admin", "content", "alembic_version"}
        assert expected_tables.issubset(set(tables))

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_migration_idempotent_upgrade() -> None:
    """Test that running upgrade multiple times is idempotent."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        database_url = f"sqlite+aiosqlite:///{db_path}"
        config = _alembic_config(database_url)
        sync_url = _sync_engine_url(database_url)

        # Run upgrade twice
        command.upgrade(config, "head")
        command.upgrade(config, "head")

        # Verify tables exist
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()

        expected_tables = {"user", "admin", "content", "alembic_version"}
        assert expected_tables.issubset(set(tables))

    finally:
        Path(db_path).unlink(missing_ok=True)