"""Application settings via Pydantic."""

import secrets
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "桐叶售电代理系统"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://tongye:tongye@localhost:5432/tongye",
        description="SQLAlchemy database URL (PostgreSQL via psycopg2).",
    )

    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing. Auto-generated if not set.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours (was 7 days)
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins. In production, set to specific frontend domain.",
    )

    SCHEDULER_ENABLED: bool = Field(
        default=False,
        description="Enable APScheduler background jobs. Defaults to False; set to True in development via env.",
    )

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()
