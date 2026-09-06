from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    bot_token: str
    admin_ids: list[int]
    database_url: str
    required_channel_id: str | None = None
    required_channel_url: str | None = None
    debug: bool = False
    rate_limit_enabled: bool = True
    rate_limit_user_per_minute: int = Field(default=20, ge=1)
    rate_limit_admin_per_minute: int = Field(default=60, ge=1)
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()