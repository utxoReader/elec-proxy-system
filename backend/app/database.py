"""SQLAlchemy database engine, session and base.

Follows jiaoyizhushou conventions with RLS region guard support.
"""

from contextvars import ContextVar
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=settings.is_development,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


# ========== Region Guard (multi-tenant isolation) ==========

_current_region: ContextVar[str | None] = ContextVar("_current_region", default=None)
_guard_enabled: ContextVar[bool] = ContextVar("_guard_enabled", default=True)


def set_current_region(region: str | None) -> None:
    """Set the current request's region for RLS filtering."""
    _current_region.set(region)


def get_current_region() -> str | None:
    """Get the current request's region."""
    return _current_region.get()


def disable_region_guard() -> None:
    """Disable region guard for admin bypass."""
    _guard_enabled.set(False)


def enable_region_guard() -> None:
    """Re-enable region guard."""
    _guard_enabled.set(True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session.

    Automatically sets the PostgreSQL RLS variable `app.current_region`
    for Row-Level Security policies when region guard is enabled.
    Use `disable_region_guard()` for admin bypass.
    """
    db = SessionLocal()
    try:
        region = get_current_region()
        if region and _guard_enabled.get():
            db.execute(
                text("SET LOCAL app.current_region = :region"),
                {"region": region},
            )
        yield db
    finally:
        db.close()
