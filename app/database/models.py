from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    telegram_file_id: str
    file_type: str
    file_name: str | None = None

    uploaded_by: int

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )