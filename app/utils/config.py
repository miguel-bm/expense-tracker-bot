from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False
    TELEGRAM_BOT_TOKEN_PROD: str
    TELEGRAM_BOT_TOKEN_DEV: str
    TELEGRAM_CHAT_ID: int
    GOOGLE_SHEETS_CREDENTIALS: str
    EXPENSES_SHEET_ID: str
    INCOMES_SHEET_ID: str
    EXPENSES_SHEET_NAME: str = "expenses"
    INCOMES_SHEET_NAME: str = "incomes"
    OPENAI_API_KEY: str
    DEFAULT_CURRENCY: str
    DEFAULT_LANGUAGE: str
    USER_MAPPING_FILE: str = "user_mapping.json"

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        return (
            self.TELEGRAM_BOT_TOKEN_DEV if self.DEBUG else self.TELEGRAM_BOT_TOKEN_PROD
        )


@lru_cache()
def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()  # type: ignore


settings = get_settings()
