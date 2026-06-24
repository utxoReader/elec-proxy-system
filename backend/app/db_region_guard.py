"""Region-based RLS guard for multi-tenant data isolation."""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import _current_region, _guard_enabled, SessionLocal


@contextmanager
def region_context(region: str) -> Generator[None, None, None]:
    token = _current_region.set(region)
    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL app.current_region = :region"), {"region": region})
        yield
    finally:
        db.close()
        _current_region.reset(token)


@contextmanager
def admin_bypass_context() -> Generator[None, None, None]:
    _guard_enabled.set(False)
    try:
        yield
    finally:
        _guard_enabled.set(True)
