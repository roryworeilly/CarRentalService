"""App configuration (pydantic-settings)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+pysqlite:///./dev.db"
    JWT_SECRET: str = "dev-insecure-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120
    HOLD_WINDOW_MINUTES: int = 15  # F.R 4.4


@lru_cache
def get_settings() -> Settings:
    return Settings()
