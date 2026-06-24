"""Usage curve template routers."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.usage_curve_template import (
    UsageCurveTemplateCreate,
    UsageCurveTemplateUpdate,
)
from app.services.usage_curve_template import UsageCurveTemplateService

router = APIRouter(prefix="/elec/usage-curve-template")


# ---------------------------------------------------------------------------
# Existing CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/page", response_model=ApiResponse)
def list_usage_curve_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template_name: str = Query(None),
    industry: str = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_db),
):
    result = UsageCurveTemplateService.list_page(db, page, page_size, template_name, industry, status)
    return ApiResponse(data=result)


@router.get("/get/{id}", response_model=ApiResponse)
def get_usage_curve_template(id: int, db: Session = Depends(get_db)):
    obj = UsageCurveTemplateService.get(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_usage_curve_template(payload: UsageCurveTemplateCreate, db: Session = Depends(get_db)):
    obj = UsageCurveTemplateService.create(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/update", response_model=ApiResponse)
def update_usage_curve_template(payload: UsageCurveTemplateUpdate, db: Session = Depends(get_db)):
    obj = UsageCurveTemplateService.update(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/delete/{id}", response_model=ApiResponse)
def delete_usage_curve_template(id: int, db: Session = Depends(get_db)):
    ok = UsageCurveTemplateService.delete(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


# ---------------------------------------------------------------------------
# New endpoints (task #47 — 13 missing endpoints)
# ---------------------------------------------------------------------------

@router.get("/enabled", response_model=ApiResponse)
def list_enabled_templates(db: Session = Depends(get_db)):
    """GET /enabled — all enabled templates."""
    items = UsageCurveTemplateService.list_enabled(db)
    return ApiResponse(data=items)


@router.get("/by-type", response_model=ApiResponse)
def list_by_type(
    template_type: int = Query(..., description="模板类型"),
    db: Session = Depends(get_db),
):
    """GET /by-type — templates filtered by template_type."""
    items = UsageCurveTemplateService.get_by_type(db, template_type)
    return ApiResponse(data=items)


@router.get("/default", response_model=ApiResponse)
def get_default_template(db: Session = Depends(get_db)):
    """GET /default — the default template."""
    obj = UsageCurveTemplateService.get_default(db)
    if not obj:
        return ApiResponse(success=False, message="No default template found")
    return ApiResponse(data=obj)


@router.put("/set-default", response_model=ApiResponse)
def set_default_template(
    id: int = Query(..., description="Template ID to set as default"),
    db: Session = Depends(get_db),
):
    """PUT /set-default — make this template the sole default."""
    ok = UsageCurveTemplateService.set_default(db, id)
    if not ok:
        return ApiResponse(success=False, message="Template not found")
    return ApiResponse(message="Default template updated")


@router.put("/update-status", response_model=ApiResponse)
def update_template_status(
    id: int = Query(..., description="Template ID"),
    status: int = Query(..., description="New status (1=enabled, 0=disabled)"),
    db: Session = Depends(get_db),
):
    """PUT /update-status — enable/disable a template."""
    ok = UsageCurveTemplateService.update_status(db, id, status)
    if not ok:
        return ApiResponse(success=False, message="Template not found")
    return ApiResponse(message="Status updated")


@router.get("/hourly-ratios", response_model=ApiResponse)
def get_hourly_ratios(
    template_id: int = Query(..., description="Template ID"),
    db: Session = Depends(get_db),
):
    """GET /hourly-ratios — 24h normal ratios as a list."""
    ratios = UsageCurveTemplateService.get_hourly_ratios(db, template_id)
    if ratios is None:
        return ApiResponse(success=False, message="Template not found")
    return ApiResponse(data=ratios)


@router.get("/hourly-ratios-by-type", response_model=ApiResponse)
def get_hourly_ratios_by_type(
    template_type: int = Query(..., description="Template type"),
    db: Session = Depends(get_db),
):
    """GET /hourly-ratios-by-type — 24h ratios for all templates of a type."""
    items = UsageCurveTemplateService.get_hourly_ratios_by_type(db, template_type)
    return ApiResponse(data=items)


class ValidateRatiosRequest(BaseModel):
    """Request body for ratio validation."""
    ratios: list[Optional[Decimal]]


@router.post("/validate-ratios", response_model=ApiResponse)
def validate_ratios(payload: ValidateRatiosRequest):
    """POST /validate-ratios — check whether 24 ratios sum to ~1.0."""
    result = UsageCurveTemplateService.validate_ratios(payload.ratios)
    return ApiResponse(data=result)


@router.get("/hourly-peak-ratios", response_model=ApiResponse)
def get_hourly_peak_ratios(
    template_id: int = Query(..., description="Template ID"),
    db: Session = Depends(get_db),
):
    """GET /hourly-peak-ratios — 24h peak-month ratios."""
    ratios = UsageCurveTemplateService.get_hourly_peak_ratios(db, template_id)
    if ratios is None:
        return ApiResponse(success=False, message="Template not found")
    return ApiResponse(data=ratios)


@router.get("/hourly-peak-ratios-by-type", response_model=ApiResponse)
def get_hourly_peak_ratios_by_type(
    template_type: int = Query(..., description="Template type"),
    db: Session = Depends(get_db),
):
    """GET /hourly-peak-ratios-by-type — peak ratios for all templates of a type."""
    items = UsageCurveTemplateService.get_hourly_peak_ratios_by_type(db, template_type)
    return ApiResponse(data=items)


@router.get("/hourly-ratios-with-peak", response_model=ApiResponse)
def get_hourly_ratios_with_peak(
    template_id: int = Query(..., description="Template ID"),
    is_peak_month: bool = Query(False, description="Whether current month is a peak month"),
    db: Session = Depends(get_db),
):
    """GET /hourly-ratios-with-peak — ratios + per-hour isPeak flag."""
    result = UsageCurveTemplateService.get_hourly_ratios_with_peak(db, template_id, is_peak_month)
    if result is None:
        return ApiResponse(success=False, message="Template not found")
    return ApiResponse(data=result)


@router.get("/hourly-ratios-by-type-with-peak", response_model=ApiResponse)
def get_hourly_ratios_by_type_with_peak(
    template_type: int = Query(..., description="Template type"),
    is_peak_month: bool = Query(False, description="Whether current month is a peak month"),
    db: Session = Depends(get_db),
):
    """GET /hourly-ratios-by-type-with-peak — ratios + peak flag for all templates of a type."""
    items = UsageCurveTemplateService.get_hourly_ratios_by_type_with_peak(db, template_type, is_peak_month)
    return ApiResponse(data=items)


@router.get("/export-excel")
def export_usage_curve_templates_excel(
    template_type: int = Query(None),
    enabled: bool = Query(None),
    db: Session = Depends(get_db),
):
    return UsageCurveTemplateService.export_excel(db, template_type, enabled)
