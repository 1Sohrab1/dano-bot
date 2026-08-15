from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: str
    database_url: str
    required_channel_id: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def admin_id_list(self) -> list[int]:
        return [
            int(admin_id.strip())
            for admin_id in self.admin_ids.split(",")
            if admin_id.strip()
        ]


settings = Settings()