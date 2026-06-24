"""Application settings — pure Python (no pydantic-settings, compatible with Python 3.14a5)."""

import os
import secrets
import pathlib
import json
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _load_env_file() -> None:
    """Load .env file manually."""
    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = val


@dataclass
class Settings:
    APP_NAME: str = "桐叶售电代理系统"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+pg8000://tongye:tongye@localhost:5432/tongye"
    SECRET_KEY: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: list = field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])
    SCHEDULER_ENABLED: bool = False

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


_settings_cache: "Settings | None" = None


def get_settings() -> Settings:
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    _load_env_file()
    s = Settings()
    s.APP_NAME = _env("APP_NAME", s.APP_NAME)
    s.APP_VERSION = _env("APP_VERSION", s.APP_VERSION)
    s.APP_ENV = _env("APP_ENV", s.APP_ENV)
    s.DATABASE_URL = _env("DATABASE_URL", s.DATABASE_URL)
    s.SECRET_KEY = _env("SECRET_KEY", secrets.token_urlsafe(32))
    s.ACCESS_TOKEN_EXPIRE_MINUTES = int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", str(s.ACCESS_TOKEN_EXPIRE_MINUTES)))
    s.ALGORITHM = _env("ALGORITHM", s.ALGORITHM)
    s.SCHEDULER_ENABLED = _env("SCHEDULER_ENABLED", str(s.SCHEDULER_ENABLED)).lower() == "true"
    cors_raw = _env("CORS_ORIGINS", "")
    if cors_raw:
        s.CORS_ORIGINS = json.loads(cors_raw)
    _settings_cache = s
    return s


settings = get_settings()
