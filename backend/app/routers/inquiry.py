"""Inquiry and quotation routers."""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.inquiry import (
    CalculatePricePayload,
    InquiryCreate,
    InquiryUpdate,
    QuotePayload,
    RejectPayload,
    StatusActionPayload,
)
from app.services import inquiry as svc

router = APIRouter(prefix="/elec")


# ---------------------------------------------------------------------------
# Existing CRUD + workflow endpoints
# ---------------------------------------------------------------------------

@router.get("/inquiry/page", response_model=ApiResponse)
def list_inquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    inquiry_status: int = Query(None),
    customer_name: str = Query(None),
    usage_month: str = Query(None, description="YYYY-MM"),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_inquiries(db, page, page_size, inquiry_status, customer_name, usage_month, agent_id)
    return ApiResponse(data=result)


@router.get("/inquiry/get/{id}", response_model=ApiResponse)
def get_inquiry(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.get_inquiry(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/inquiry/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(payload: InquiryCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.create_inquiry(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id, "inquiry_no": obj.inquiry_no})


@router.put("/inquiry/update", response_model=ApiResponse)
def update_inquiry(payload: InquiryUpdate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.update_inquiry(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/inquiry/delete/{id}", response_model=ApiResponse)
def delete_inquiry(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = svc.delete_inquiry(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.post("/inquiry/{id}/quote", response_model=ApiResponse)
def quote_inquiry(id: int, payload: QuotePayload, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.quote_inquiry(db, id, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Quoted", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/accept", response_model=ApiResponse)
def accept_inquiry(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.accept_inquiry(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Accepted", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/reject", response_model=ApiResponse)
def reject_inquiry(
    id: int,
    payload: Optional[RejectPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    reason = payload.reject_reason if payload else None
    obj = svc.reject_inquiry(db, id, reason)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Rejected", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/cooperate", response_model=ApiResponse)
def cooperate_inquiry(
    id: int,
    payload: Optional[StatusActionPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    payload = payload or StatusActionPayload()
    obj = svc.cooperate_inquiry(
        db,
        id,
        cooperation_start_date=payload.cooperation_start_date,
        cooperation_end_date=payload.cooperation_end_date,
    )
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Cooperated", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/terminate", response_model=ApiResponse)
def terminate_inquiry(
    id: int,
    payload: Optional[StatusActionPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    payload = payload or StatusActionPayload()
    obj = svc.terminate_inquiry(db, id, terminate_date=payload.terminate_date)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Terminated", data={"id": obj.id, "status": obj.inquiry_status})


@router.get("/inquiry/statistics", response_model=ApiResponse)
def inquiry_statistics(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    result = svc.get_statistics(db)
    return ApiResponse(data=result)


@router.get("/inquiry/export", response_class=StreamingResponse)
def export_inquiries(
    inquiry_status: int = Query(None),
    customer_name: str = Query(None),
    usage_month: str = Query(None),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    data = svc.export_inquiries(db, inquiry_status, customer_name, usage_month, agent_id)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inquiries.xlsx"},
    )


@router.post("/inquiry/calculate-price", response_model=ApiResponse)
def calculate_price(payload: CalculatePricePayload, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    result = svc.calculate_price(db, payload)
    return ApiResponse(data=result)


@router.post("/inquiry/{id}/upload-consumption-data", response_model=ApiResponse)
def upload_consumption_data(
    id: int,
    file: UploadFile,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    result = svc.upload_consumption_data(db, id, file)
    if not result:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Uploaded", data=result)


@router.get("/inquiry/{id}/consumption-data", response_model=ApiResponse)
def get_consumption_data(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = svc.get_consumption_data(db, id)
    if data is None:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=data)


# ---------------------------------------------------------------------------
# Task #45 — Missing inquiry endpoints (23 new)
# ---------------------------------------------------------------------------

# ── Query / filter endpoints ──────────────────────────────────────────────

@router.get("/inquiry/generate-no", response_model=ApiResponse)
def generate_no(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a new inquiry number without creating a record."""
    return ApiResponse(data={"inquiry_no": svc.generate_inquiry_no(db)})


@router.get("/inquiry/list", response_model=ApiResponse)
def list_all_inquiries(
    inquiry_status: int = Query(None),
    customer_name: str = Query(None),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_all(db, inquiry_status, customer_name, agent_id)
    return ApiResponse(data=items)


@router.get("/inquiry/simple-list", response_model=ApiResponse)
def simple_list(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.simple_list(db)
    return ApiResponse(data=items)


@router.get("/inquiry/by-agent/{agent_id}", response_model=ApiResponse)
def list_by_agent(agent_id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.list_by_agent(db, agent_id)
    return ApiResponse(data=items)


@router.get("/inquiry/pending", response_model=ApiResponse)
def list_pending_inquiries(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.list_pending(db)
    return ApiResponse(data=items)


@router.get("/inquiry/pending-quote-list", response_model=ApiResponse)
def list_pending_quotes(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.list_pending_quotes(db)
    return ApiResponse(data=items)


@router.get("/inquiry/expired", response_model=ApiResponse)
def list_expired_inquiries(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.list_expired(db)
    return ApiResponse(data=items)


@router.get("/inquiry/list-by-customer", response_model=ApiResponse)
def list_by_customer(
    customer_name: str = Query(..., description="Customer name (partial match)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_by_customer(db, customer_name)
    return ApiResponse(data=items)


@router.get("/inquiry/list-by-status", response_model=ApiResponse)
def list_by_status(
    inquiry_status: int = Query(..., description="Status code"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_by_status(db, inquiry_status)
    return ApiResponse(data=items)


@router.get("/inquiry/count-by-status", response_model=ApiResponse)
def count_by_status(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    result = svc.count_by_status(db)
    return ApiResponse(data=result)


@router.get("/inquiry/list-by-time-range", response_model=ApiResponse)
def list_by_time_range(
    start_date: str = Query(..., description="ISO date string"),
    end_date: str = Query(..., description="ISO date string"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_by_time_range(db, start_date, end_date)
    return ApiResponse(data=items)


@router.get("/inquiry/list-by-month", response_model=ApiResponse)
def list_by_month(
    usage_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_by_month(db, usage_month)
    return ApiResponse(data=items)


@router.get("/inquiry/list-by-year", response_model=ApiResponse)
def list_by_year(
    year: str = Query(..., description="YYYY"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_by_year(db, year)
    return ApiResponse(data=items)


class BatchUpdateStatusPayload(BaseModel):
    ids: list[int]
    inquiry_status: int


@router.put("/inquiry/batch-update-status", response_model=ApiResponse)
def batch_update_status(payload: BatchUpdateStatusPayload, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    count = svc.batch_update_status(db, payload.ids, payload.inquiry_status)
    return ApiResponse(message=f"Updated {count} inquiries", data={"count": count})


# ── Lifecycle endpoints ───────────────────────────────────────────────────

@router.post("/inquiry/{id}/submit", response_model=ApiResponse)
def submit_inquiry(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.submit_inquiry(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Submitted", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/reject-inquiry", response_model=ApiResponse)
def reject_inquiry_cooperation(
    id: int,
    payload: Optional[RejectPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    reason = payload.reject_reason if payload else None
    obj = svc.reject_inquiry_cooperation(db, id, reason)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Rejected", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/accept-quote-by-customer", response_model=ApiResponse)
def accept_quote_by_customer(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.accept_quote_by_customer(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Accepted by customer", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/approve-quote", response_model=ApiResponse)
def approve_quote(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.approve_quote(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Approved", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/reject-quote", response_model=ApiResponse)
def reject_quote_admin(
    id: int,
    payload: Optional[RejectPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    reason = payload.reject_reason if payload else None
    obj = svc.reject_quote_admin(db, id, reason)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Quote rejected", data={"id": obj.id, "status": obj.inquiry_status})


class CooperationConfirmPayload(BaseModel):
    cooperation_start_date: Optional[date] = None
    cooperation_end_date: Optional[date] = None


@router.post("/inquiry/{id}/confirm-cooperation", response_model=ApiResponse)
def confirm_cooperation(
    id: int,
    payload: Optional[CooperationConfirmPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    payload = payload or CooperationConfirmPayload()
    obj = svc.confirm_cooperation(
        db, id,
        cooperation_start_date=payload.cooperation_start_date,
        cooperation_end_date=payload.cooperation_end_date,
    )
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Cooperation confirmed", data={"id": obj.id, "status": obj.inquiry_status})


class TerminateCooperationPayload(BaseModel):
    terminate_date: Optional[date] = None


@router.post("/inquiry/{id}/terminate-cooperation", response_model=ApiResponse)
def terminate_cooperation(
    id: int,
    payload: Optional[TerminateCooperationPayload] = None,
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db),
):
    payload = payload or TerminateCooperationPayload()
    obj = svc.terminate_cooperation(db, id, payload.terminate_date)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Cooperation terminated", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/{id}/mark-expired", response_model=ApiResponse)
def mark_expired(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = svc.mark_expired(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Marked expired", data={"id": obj.id, "status": obj.inquiry_status})


@router.post("/inquiry/batch-process-expired", response_model=ApiResponse)
def batch_process_expired(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    count = svc.batch_process_expired(db)
    return ApiResponse(message=f"Processed {count} expired inquiries", data={"count": count})


# ── Pricing engine endpoints ──────────────────────────────────────────────

@router.get("/inquiry/{id}/calculate-quote", response_model=ApiResponse)
def calculate_quote_auto(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Basic auto-quote using the full pricing engine."""
    result = svc.calculate_quote_auto(db, id)
    return ApiResponse(data=result)


@router.get("/inquiry/{id}/calculate-advanced-quote", response_model=ApiResponse)
def calculate_advanced_quote(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Advanced quote with full detail (both packages)."""
    result = svc.calculate_advanced_quote(db, id)
    return ApiResponse(data=result)


@router.get("/inquiry/{id}/calculate-dynamic-pricing", response_model=ApiResponse)
def calculate_dynamic_pricing(
    id: int,
    price_difference: Decimal = Query(..., description="Price difference to calculate with"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """What-if calculator with user-supplied price difference."""
    result = svc.calculate_dynamic_pricing(db, id, price_difference)
    return ApiResponse(data=result)


# ── Consumption summary / quote export ────────────────────────────────────

@router.get("/inquiry/{id}/consumption-summary", response_model=ApiResponse)
def get_consumption_summary(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = svc.get_consumption_summary(db, id)
    if data is None:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=data)


@router.get("/inquiry/{id}/export-quote-result", response_class=StreamingResponse)
def export_quote_result(id: int, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = svc.export_quote_result(db, id)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=quote_{id}.xlsx"},
    )
