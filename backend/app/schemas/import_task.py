"""Pydantic schemas for import task."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ImportTaskBase(BaseModel):
    """Common fields for import task."""

    task_id: Optional[str] = Field(None, max_length=50)
    original_filename: Optional[str] = Field(None, max_length=200)
    file_path: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = None
    task_status: Optional[int] = Field(0)
    progress: Optional[int] = Field(0)
    total_rows: Optional[int] = None
    success_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    skipped_rows: Optional[int] = None
    error_message: Optional[str] = None
    progress_message: Optional[str] = None
    result_summary: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    region: Optional[str] = Field(None, max_length=20)


class ImportTaskOut(ImportTaskBase):
    """Output schema."""

    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class ImportTaskPageOut(BaseModel):
    """Paginated output matching `paginate_query` shape."""

    list: list[ImportTaskOut]
    total: int
    pageNo: int
    pageSize: int
