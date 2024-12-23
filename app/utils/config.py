from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: int
    GOOGLE_SHEETS_CREDENTIALS: str
    EXPENSES_SHEET_ID: str
    OPENAI_API_KEY: str
    DEFAULT_CURRENCY: str
    DEFAULT_LANGUAGE: str

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
