"""Base model mixins and common utilities.

Follows jiaoyizhushou conventions:
- UUID primary keys where appropriate
- created_at / updated_at timestamps with timezone
- Soft delete via deleted_at nullable timestamp
- region column for multi-tenant isolation
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database import Base


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime | None]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )


class SoftDeleteMixin:
    """Adds deleted_at column for soft deletes."""

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(DateTime(timezone=True), nullable=True, default=None)


class RegionMixin:
    """Adds region column for multi-tenant data isolation."""

    @declared_attr
    def region(cls) -> Mapped[str | None]:
        return mapped_column(String(20), nullable=True, index=True)


class AgentScopedMixin:
    """Adds agent_id for agent-level data scoping."""

    @declared_attr
    def agent_id(cls) -> Mapped[int | None]:
        return mapped_column(nullable=True, index=True)
