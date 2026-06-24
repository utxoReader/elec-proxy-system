"""Base CRUD utilities."""

from typing import Generic, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session

ModelType = TypeVar("ModelType")


def paginate_query(
    db: Session,
    query: Query,
    page_no: int = 1,
    page_size: int = 20,
) -> dict:
    """Paginate a SQLAlchemy query and return a standard page result.

    Args:
        db: SQLAlchemy session.
        query: Query object (already filtered).
        page_no: 1-based page number.
        page_size: Items per page.

    Returns:
        Dict with list, total, pageNo, pageSize.
    """
    if page_no < 1:
        page_no = 1
    if page_size < 1:
        page_size = 20

    total = query.count()
    items = (
        query.offset((page_no - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "list": items,
        "total": total,
        "pageNo": page_no,
        "pageSize": page_size,
    }


def get_or_404(db: Session, model: type[ModelType], record_id: int) -> ModelType:
    """Fetch a record by ID or raise 404."""
    record = db.query(model).filter(model.id == record_id).first()  # type: ignore[attr-defined]
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found",
        )
    return record
