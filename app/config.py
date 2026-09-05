from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: list[int]
    database_url: str
    required_channel_id: str | None = None
    debug: bool = False
    rate_limit_enabled: bool = True
    rate_limit_user_per_minute: int = Field(default=20, ge=1)
    rate_limit_admin_per_minute: int = Field(default=60, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()