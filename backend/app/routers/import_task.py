"""Import task routers."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.services.import_task import ImportTaskService

router = APIRouter(prefix="/elec/import-task")


@router.get("/page", response_model=ApiResponse)
def list_import_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_status: int = Query(None),
    original_filename: str = Query(None),
    db: Session = Depends(get_db),
):
    result = ImportTaskService.list_page(db, page, page_size, task_status, original_filename)
    return ApiResponse(data=result)


@router.get("/get/{id}", response_model=ApiResponse)
def get_import_task(id: int, db: Session = Depends(get_db)):
    obj = ImportTaskService.get(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)
