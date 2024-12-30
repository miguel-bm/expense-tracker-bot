from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
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

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()  # type: ignore


settings = get_settings()
