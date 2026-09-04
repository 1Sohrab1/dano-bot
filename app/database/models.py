from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")


class ContentState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Content(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_chat_id: int
    source_message_id: int
    content_type: str
    code: str = Field(unique=True, index=True)
    state: str = Field(default=ContentState.ACTIVE, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = Field(default=None)