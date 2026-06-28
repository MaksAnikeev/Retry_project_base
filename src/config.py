from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    MODE: Literal["TEST", "LOCAL", "DEV", "PROD"]

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    REPORT_SERVICE_URL: str
    REPORT_SERVICE_TIMEOUT: int
    REPORT_SERVICE_RETRIES: int

    LOG_LEVEL: str = "INFO"

    MAX_CONSECUTIVE_FAILURES: int
    CB_WAIT_SECONDS: int
    MAX_CB_RETRIES: int

    REDIS_URL: str

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASS)
        return f"postgresql+asyncpg://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()