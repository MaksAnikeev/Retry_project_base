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

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT_TYPE: str = ""

    REDIS_URL: str

    # --------------------RETRY-------------------------
    STOP_RETRY_AFTER_ATTEMPT_BASE: int
    EXPONENTIAL_JITTER_INTERVAL_BASE: int
    EXPONENTIAL_JITTER_MAX_BASE: int
    EXPONENTIAL_JITTER_EXP_BASE: int
    EXPONENTIAL_JITTER_BASE: float
    STOP_RETRY_AFTER_ATTEMPT_FAST: int
    EXPONENTIAL_JITTER_INTERVAL_FAST: int
    EXPONENTIAL_JITTER_MAX_FAST: int

    # --------------------CIRCUIT_BREAKER-------------------------
    CB_FAILURE_THRESHOLD_STANDARD: int
    CB_RECOVERY_TIMEOUT_STANDARD: int

    # --------------------WORKER-------------------------
    BATCH_SIZE: int
    MAX_BATCH_COUNT: int
    MAX_REPORT_ATTEMPTS: int

    # --------------------OUTBOX_WORKER-------------------------
    OUTBOX_BATCH_SIZE: int
    OUTBOX_MAX_BATCH_COUNT: int
    OUTBOX_MAX_ATTEMPTS: int
    OUTBOX_SENT_RETRIES: int
    ORDER_TOPIC: str

    # --------------------KAFKA-------------------------
    KAFKA_BOOTSTRAP_SERVERS: str

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASS)
        return f"postgresql+asyncpg://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()