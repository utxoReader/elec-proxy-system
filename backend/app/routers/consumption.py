"""Consumption data routers.

Covers:
- CustomerDailyConsumption CRUD + batch create + statistics
- CustomerHourlyConsumption CRUD
- Point96Data CRUD + convert-to-daily
- Conversion helpers (point96-to-24h, peak-valley-to-24h, fill-missing, copy-data)
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.consumption import (
    CustomerDailyConsumptionCreate,
    CustomerDailyConsumptionUpdate,
    CustomerHourlyConsumptionCreate,
    CustomerHourlyConsumptionUpdate,
    Point96DataCreate,
)
from app.services import conversion as conversion_svc
from app.services.consumption import (
    CustomerDailyConsumptionService,
    CustomerHourlyConsumptionService,
    HourlyConsumptionExtendedService,
    Point96DataService,
    Point96ExtendedService,
    CustomerSavingsService,
)
from app.services.usage_curve_template import UsageCurveTemplateService

router = APIRouter(prefix="/elec")


# ==================== CustomerDailyConsumption ====================

@router.get("/daily-consumption/page", response_model=ApiResponse)
def list_daily_consumption(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_account_id: int = Query(None),
    data_month: str = Query(None, description="YYYY-MM"),
    data_date: date = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    result = CustomerDailyConsumptionService.list_page(
        db, page, page_size, customer_account_id, data_month, data_date
    )
    return ApiResponse(data=result)


@router.get("/daily-consumption/get/{id}", response_model=ApiResponse)
def get_daily_consumption(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerDailyConsumptionService.get(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/daily-consumption/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_daily_consumption(payload: CustomerDailyConsumptionCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerDailyConsumptionService.create(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/daily-consumption/update", response_model=ApiResponse)
def update_daily_consumption(payload: CustomerDailyConsumptionUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerDailyConsumptionService.update(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/daily-consumption/delete/{id}", response_model=ApiResponse)
def delete_daily_consumption(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = CustomerDailyConsumptionService.delete(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.post("/daily-consumption/batch-create", response_model=ApiResponse)
def batch_create_daily_consumption(payload: list[CustomerDailyConsumptionCreate], db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    count = CustomerDailyConsumptionService.batch_create(db, payload)
    return ApiResponse(message=f"Created {count} records", data={"count": count})


@router.get("/daily-consumption/statistics", response_model=ApiResponse)
def daily_consumption_statistics(
    customer_account_id: int = Query(None),
    data_month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    result = CustomerDailyConsumptionService.statistics(db, customer_account_id, data_month)
    return ApiResponse(data=result)


# ==================== CustomerHourlyConsumption ====================

@router.get("/hourly-consumption/page", response_model=ApiResponse)
def list_hourly_consumption(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_account_id: int = Query(None),
    data_month: str = Query(None, description="YYYY-MM"),
    data_date: date = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    result = CustomerHourlyConsumptionService.list_page(
        db, page, page_size, customer_account_id, data_month, data_date
    )
    return ApiResponse(data=result)


@router.get("/hourly-consumption/get/{id}", response_model=ApiResponse)
def get_hourly_consumption(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerHourlyConsumptionService.get(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/hourly-consumption/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_hourly_consumption(payload: CustomerHourlyConsumptionCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerHourlyConsumptionService.create(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/hourly-consumption/update", response_model=ApiResponse)
def update_hourly_consumption(payload: CustomerHourlyConsumptionUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = CustomerHourlyConsumptionService.update(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/hourly-consumption/delete/{id}", response_model=ApiResponse)
def delete_hourly_consumption(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = CustomerHourlyConsumptionService.delete(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


# ==================== Point96Data ====================

@router.get("/point96/page", response_model=ApiResponse)
def list_point96(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_account_id: int = Query(None),
    data_month: str = Query(None, description="YYYY-MM"),
    data_date: date = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    result = Point96DataService.list_page(db, page, page_size, customer_account_id, data_month, data_date)
    return ApiResponse(data=result)


@router.get("/point96/get/{id}", response_model=ApiResponse)
def get_point96(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = Point96DataService.get(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/point96/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_point96(payload: Point96DataCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = Point96DataService.create(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.delete("/point96/delete/{id}", response_model=ApiResponse)
def delete_point96(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = Point96DataService.delete(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.get("/point96/import-template")
def download_point96_import_template():
    """Download blank 96-point data import template."""
    from app.services.excel_utils import export_to_response

    headers = ["客户账户ID", "数据日期", "客户名称"] + [f"时段{i:02d}" for i in range(1, 97)]
    data = [["1", "2026-01-01", "示例客户"] + ["0.0"] * 96]
    return export_to_response(headers, data, "96点数据导入模板.xlsx", "导入模板")


@router.post("/point96/import", response_model=ApiResponse)
def import_point96(file: UploadFile, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    result = Point96DataService.import_from_file(db, file)
    return ApiResponse(message="Imported", data=result)


@router.post("/point96/convert-to-daily/{id}", response_model=ApiResponse)
def convert_point96_to_daily(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    result = Point96DataService.convert_to_daily(db, id)
    return ApiResponse(message="Converted", data=result)


# ==================== Conversion helpers ====================

class Point96To24hPayload(BaseModel):
    point96_id: int

    model_config = ConfigDict(extra="forbid")


class PeakValleyTo24hPayload(BaseModel):
    template_id: int
    peak: Decimal
    high: Decimal
    normal: Decimal
    valley: Decimal
    is_peak_month: bool = False

    model_config = ConfigDict(extra="forbid")


class FillMissingPayload(BaseModel):
    customer_account_id: int
    month: str

    model_config = ConfigDict(extra="forbid")


class CopyDataPayload(BaseModel):
    source_customer_id: int
    target_customer_id: int
    month: str

    model_config = ConfigDict(extra="forbid")


@router.post("/conversion/point96-to-24h", response_model=ApiResponse)
def convert_point96_to_24h(payload: Point96To24hPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = Point96DataService.get(db, payload.point96_id)
    if not obj:
        return ApiResponse(success=False, message="Point96 record not found")
    hours = conversion_svc.point96_to_24h(obj)
    return ApiResponse(data={"point96_id": payload.point96_id, "hours": hours})


@router.post("/conversion/peak-valley-to-24h", response_model=ApiResponse)
def convert_peak_valley_to_24h(payload: PeakValleyTo24hPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    template = UsageCurveTemplateService.get(db, payload.template_id)
    if not template:
        return ApiResponse(success=False, message="Template not found")
    hours = conversion_svc.peak_valley_to_24h(
        payload.peak,
        payload.high,
        payload.normal,
        payload.valley,
        template,
        payload.is_peak_month,
    )
    return ApiResponse(data={"template_id": payload.template_id, "hours": hours})


@router.post("/conversion/fill-missing", response_model=ApiResponse)
def fill_missing_daily(payload: FillMissingPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    result = conversion_svc.fill_missing_daily_data(db, payload.customer_account_id, payload.month)
    return ApiResponse(data=result)


@router.post("/conversion/copy-data", response_model=ApiResponse)
def copy_daily_data(payload: CopyDataPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    result = conversion_svc.copy_daily_data(
        db, payload.source_customer_id, payload.target_customer_id, payload.month
    )
    return ApiResponse(data=result)


@router.get("/customer-daily-consumption/export-excel")
def export_daily_consumption_excel(
    customer_account_id: int = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Export daily consumption as Excel."""
    return CustomerDailyConsumptionService.export_excel(
        db, customer_account_id, start_date, end_date
    )


@router.get("/customer-hourly-consumption/export-excel")
def export_hourly_consumption_excel(
    customer_account_id: int = Query(None),
    data_date: str = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Export hourly consumption as Excel."""
    return CustomerHourlyConsumptionService.export_excel(
        db, customer_account_id, data_date
    )


# ===========================================================================
# Task #46 — Extended hourly consumption endpoints
# ===========================================================================

@router.get("/hourly-consumption/list", response_model=ApiResponse)
def list_hourly_all(
    customer_account_id: int = Query(None),
    data_month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """List all hourly records without pagination."""
    result = HourlyConsumptionExtendedService.list_all(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/customer-month-data", response_model=ApiResponse)
def hourly_customer_month_data(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Get all hourly data for a customer in a specific month."""
    result = HourlyConsumptionExtendedService.get_month_data(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/customer-daily", response_model=ApiResponse)
def hourly_customer_daily(
    customer_account_id: int = Query(...),
    data_date: date = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Get hourly data for a customer on a specific date."""
    result = HourlyConsumptionExtendedService.get_daily_data(db, customer_account_id, data_date)
    if not result:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=result)


@router.get("/hourly-consumption/statistics", response_model=ApiResponse)
def hourly_statistics(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Monthly aggregated statistics for hourly consumption."""
    result = HourlyConsumptionExtendedService.get_statistics(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/time-period-statistics", response_model=ApiResponse)
def hourly_time_period_statistics(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Peak/high/normal/valley breakdown statistics."""
    result = HourlyConsumptionExtendedService.get_time_period_statistics(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/trend", response_model=ApiResponse)
def hourly_trend(
    customer_account_id: int = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Daily consumption trend between two dates."""
    result = HourlyConsumptionExtendedService.get_trend(db, customer_account_id, start_date, end_date)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/check-completeness", response_model=ApiResponse)
def hourly_check_completeness(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Check whether data exists for every day in the month."""
    result = HourlyConsumptionExtendedService.check_completeness(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/hourly-consumption/count-records", response_model=ApiResponse)
def hourly_count_records(
    customer_account_id: int = Query(None),
    data_month: str = Query(None),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Count total hourly records matching filters."""
    count = HourlyConsumptionExtendedService.count_records(db, customer_account_id, data_month)
    return ApiResponse(data={"count": count})


@router.get("/hourly-consumption/daily-summary", response_model=ApiResponse)
def hourly_daily_summary(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Per-day summary for a customer in a month."""
    result = HourlyConsumptionExtendedService.get_daily_summary(db, customer_account_id, data_month)
    return ApiResponse(data=result)


class Submit24HourPayload(BaseModel):
    customer_account_id: int
    data_date: date
    hours: list[Optional[Decimal]] = Field(..., min_length=24, max_length=24)
    customer_name: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


@router.post("/hourly-consumption/submit-24hour-data", response_model=ApiResponse)
def hourly_submit_24hour(payload: Submit24HourPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Submit or update 24-hour consumption data for a specific date."""
    result = HourlyConsumptionExtendedService.submit_24hour_data(
        db, payload.customer_account_id, payload.data_date, payload.hours, payload.customer_name
    )
    return ApiResponse(message="Saved", data=result)


class SplitTimeOfUsePayload(BaseModel):
    customer_account_id: int
    data_date: date
    peak: Decimal
    high: Decimal
    normal: Decimal
    valley: Decimal

    model_config = ConfigDict(extra="forbid")


@router.post("/hourly-consumption/split-from-time-of-use", response_model=ApiResponse)
def hourly_split_from_tou(payload: SplitTimeOfUsePayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Distribute peak/high/normal/valley totals across 24 hours."""
    result = HourlyConsumptionExtendedService.split_from_time_of_use(
        db, payload.customer_account_id, payload.data_date,
        payload.peak, payload.high, payload.normal, payload.valley,
    )
    return ApiResponse(data=result)


@router.delete("/hourly-consumption/delete-monthly-data", response_model=ApiResponse)
def hourly_delete_monthly(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete all hourly records for a customer in a month."""
    count = HourlyConsumptionExtendedService.delete_monthly_data(db, customer_account_id, data_month)
    return ApiResponse(message=f"Deleted {count} records", data={"count": count})


@router.delete("/hourly-consumption/delete-daily-data", response_model=ApiResponse)
def hourly_delete_daily(
    customer_account_id: int = Query(...),
    data_date: date = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete hourly records for a customer on a specific date."""
    count = HourlyConsumptionExtendedService.delete_daily_data(db, customer_account_id, data_date)
    return ApiResponse(message=f"Deleted {count} records", data={"count": count})


class BatchImportHourlyPayload(BaseModel):
    records: list[dict[str, Any]]

    model_config = ConfigDict(extra="forbid")


@router.post("/hourly-consumption/batch-import", response_model=ApiResponse)
def hourly_batch_import(payload: BatchImportHourlyPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Batch import 24h consumption records."""
    count = HourlyConsumptionExtendedService.batch_import(db, payload.records)
    return ApiResponse(message=f"Imported {count} records", data={"count": count})


class ConvertInquiryPayload(BaseModel):
    inquiry_id: int
    customer_account_id: int

    model_config = ConfigDict(extra="forbid")


@router.post("/hourly-consumption/convert-inquiry-to-customer", response_model=ApiResponse)
def hourly_convert_inquiry(payload: ConvertInquiryPayload, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Copy consumption data from an inquiry to a customer account."""
    result = HourlyConsumptionExtendedService.convert_inquiry_to_customer(
        db, payload.inquiry_id, payload.customer_account_id
    )
    return ApiResponse(message="Converted", data=result)


# ─── Extended Point96 endpoints ───────────────────────────────────────────

@router.get("/point96/get-by-customer-date", response_model=ApiResponse)
def point96_by_customer_date(
    customer_account_id: int = Query(...),
    data_date: date = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Get 96-point data for a customer on a specific date."""
    result = Point96ExtendedService.get_by_customer_date(db, customer_account_id, data_date)
    if not result:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=result)


@router.get("/point96/list-by-customer", response_model=ApiResponse)
def point96_list_by_customer(
    customer_account_id: int = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """List all 96-point records for a customer."""
    result = Point96ExtendedService.list_by_customer(db, customer_account_id)
    return ApiResponse(data=result)


@router.delete("/point96/delete-by-customer-date", response_model=ApiResponse)
def point96_delete_by_customer_date(
    customer_account_id: int = Query(...),
    data_date: date = Query(...),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete 96-point records for a customer on a specific date."""
    count = Point96ExtendedService.delete_by_customer_date(db, customer_account_id, data_date)
    return ApiResponse(message=f"Deleted {count} records", data={"count": count})


# ===========================================================================
# Task #48 — Customer savings analysis
# ===========================================================================

@router.get("/customer-savings/preview", response_model=ApiResponse)
def customer_savings_preview(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Preview customer savings vs grid fee for a month."""
    result = CustomerSavingsService.preview_savings(db, customer_account_id, data_month)
    return ApiResponse(data=result)


@router.get("/customer-savings/export-excel")
def customer_savings_export_excel(
    customer_account_id: int = Query(...),
    data_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
):
    """Export customer savings detail as Excel."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO

    content = CustomerSavingsService.export_excel(db, customer_account_id, data_month)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=客户节约分析_{data_month}.xlsx"},
    )
