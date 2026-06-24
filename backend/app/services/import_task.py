"""Import task business logic."""

from typing import Optional

from sqlalchemy.orm import Session

from app.crud.base import get_or_404, paginate_query
from app.models.import_task import ImportTask


def _import_task_out(obj: ImportTask) -> dict:
    return {
        "id": obj.id,
        "task_id": obj.task_id,
        "original_filename": obj.original_filename,
        "file_path": obj.file_path,
        "file_size": obj.file_size,
        "task_status": obj.task_status,
        "progress": obj.progress,
        "total_rows": obj.total_rows,
        "success_rows": obj.success_rows,
        "failed_rows": obj.failed_rows,
        "skipped_rows": obj.skipped_rows,
        "error_message": obj.error_message,
        "progress_message": obj.progress_message,
        "result_summary": obj.result_summary,
        "start_time": obj.start_time,
        "end_time": obj.end_time,
        "region": obj.region,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


class ImportTaskService:
    """Read-only service for ImportTask."""

    @staticmethod
    def list_page(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        task_status: Optional[int] = None,
        original_filename: Optional[str] = None,
    ) -> dict:
        q = db.query(ImportTask).filter(ImportTask.deleted_at.is_(None))
        if task_status is not None:
            q = q.filter(ImportTask.task_status == task_status)
        if original_filename:
            q = q.filter(ImportTask.original_filename.ilike(f"%{original_filename}%"))
        q = q.order_by(ImportTask.created_at.desc())
        page_result = paginate_query(db, q, page, page_size)
        page_result["list"] = [_import_task_out(item) for item in page_result["list"]]
        return page_result

    @staticmethod
    def get(db: Session, record_id: int) -> Optional[dict]:
        obj = (
            db.query(ImportTask)
            .filter(ImportTask.id == record_id, ImportTask.deleted_at.is_(None))
            .first()
        )
        return _import_task_out(obj) if obj else None
