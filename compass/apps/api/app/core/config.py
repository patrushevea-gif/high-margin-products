from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: str = "development"
    secret_key: str = "change-me"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://compass:compass@localhost:5432/compass"
    redis_url: str = "redis://localhost:6379"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Integrations (optional)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    bitrix24_webhook_url: str = ""
    obsidian_vault_path: str = ""

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
