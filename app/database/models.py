from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Admin(SQLModel, table=True):
    user_id: int = Field(primary_key=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )