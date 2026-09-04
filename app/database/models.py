from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")


class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    telegram_file_id: str
    file_name: str

    uploaded_by: int = Field(foreign_key="user.id")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )