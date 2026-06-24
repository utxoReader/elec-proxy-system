"""Inquiry and quotation business logic."""

import json
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.crud.base import paginate_query
from app.models.customer_account import CustomerAccount
from app.models.inquiry import Inquiry
from app.schemas.inquiry import (
    CalculatePricePayload,
    InquiryCreate,
    InquiryUpdate,
    QuotePayload,
)
from app.services.conversion import peak_valley_to_24h
from app.services.usage_curve_template import UsageCurveTemplateService


# Status constants
STATUS_PENDING = 1
STATUS_QUOTED = 2
STATUS_ACCEPTED = 3
STATUS_REJECTED = 4
STATUS_EXPIRED = 5
STATUS_COOPERATED = 6

_STATUS_LABELS = {
    STATUS_PENDING: "待处理",
    STATUS_QUOTED: "已报价",
    STATUS_ACCEPTED: "已接受",
    STATUS_REJECTED: "已拒绝",
    STATUS_EXPIRED: "已过期",
    STATUS_COOPERATED: "已合作",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _inquiry_out(obj: Inquiry) -> dict:
    """Convert ORM object to frontend-friendly dict."""
    data = {
        "id": obj.id,
        "inquiry_no": obj.inquiry_no,
        "agent_id": obj.agent_id,
        "agent_name": obj.agent_name,
        "customer_name": obj.customer_name,
        "contact_person": obj.contact_person,
        "contact_phone": obj.contact_phone,
        "voltage_level": obj.voltage_level,
        "customer_type": obj.customer_type,
        "usage_month": obj.usage_month,
        "estimated_monthly_consumption": obj.estimated_monthly_consumption,
        "usage_address": obj.usage_address,
        "industry_type": obj.industry_type,
        "enterprise_feature": obj.enterprise_feature,
        "production_time": obj.production_time,
        "data_submit_type": obj.data_submit_type,
        "peak_consumption": obj.peak_consumption,
        "high_consumption": obj.high_consumption,
        "normal_consumption": obj.normal_consumption,
        "valley_consumption": obj.valley_consumption,
        "usage_curve_template_id": obj.usage_curve_template_id,
        "usage_curve_template_name": obj.usage_curve_template_name,
        "inquiry_status": obj.inquiry_status,
        "is_second_inquiry": obj.is_second_inquiry,
        "reject_reason": obj.reject_reason,
        "customer_confirm_time": obj.customer_confirm_time,
        "admin_confirm_time": obj.admin_confirm_time,
        "cooperation_start_date": obj.cooperation_start_date,
        "cooperation_end_date": obj.cooperation_end_date,
        "terminate_date": obj.terminate_date,
        "quoted_at": obj.quoted_at,
        "quote_valid_until": obj.quote_valid_until,
        "recommended_package_type": obj.recommended_package_type,
        "price_difference": obj.price_difference,
        "estimated_monthly_fee": obj.estimated_monthly_fee,
        "estimated_savings": obj.estimated_savings,
        "savings_rate": obj.savings_rate,
        "remark": obj.remark,
        "consumption_data_json": _parse_json(obj.consumption_data_json),
        "consumption_summary": obj.consumption_summary,
        "region": obj.region,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "deleted_at": obj.deleted_at,
    }
    return data


def _generate_inquiry_no(db: Session) -> str:
    """Generate inquiry number: XJ{YYYYMMDD}{4-digit sequence}."""
    today_str = _now().strftime("%Y%m%d")
    prefix = f"XJ{today_str}"
    count = (
        db.query(func.count(Inquiry.id))
        .filter(
            Inquiry.inquiry_no.like(f"{prefix}%"),
            Inquiry.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )
    seq = count + 1
    return f"{prefix}{seq:04d}"


def _fill_customer_defaults(
    db: Session, data: InquiryCreate | InquiryUpdate, values: dict
) -> dict:
    """Fill agent/voltage info from existing customer when customer_name matches."""
    customer_name = values.get("customer_name")
    if not customer_name:
        return values

    customer = (
        db.query(CustomerAccount)
        .filter(
            CustomerAccount.deleted_at.is_(None),
            CustomerAccount.customer_name.ilike(customer_name),
        )
        .first()
    )
    if not customer:
        return values

    for field in (
        "agent_id",
        "agent_name",
        "voltage_level",
        "customer_type",
        "contact_person",
        "contact_phone",
        "industry_type",
        "enterprise_feature",
        "production_time",
        "usage_address",
    ):
        if values.get(field) is None and getattr(customer, field, None) is not None:
            values[field] = getattr(customer, field)
    return values


def _prepare_consumption_data(
    db: Session, data: InquiryCreate, values: dict
) -> dict:
    """Process consumption data based on data_submit_type."""
    submit_type = values.get("data_submit_type")
    consumption_json = values.pop("consumption_data_json", None)

    if submit_type == 1:
        # 24h hourly data
        if consumption_json:
            values["consumption_data_json"] = json.dumps(consumption_json, ensure_ascii=False)
    elif submit_type == 2:
        # peak-valley: store totals and optionally derive 24h from template
        values["peak_consumption"] = values.get("peak_consumption") or Decimal("0")
        values["high_consumption"] = values.get("high_consumption") or Decimal("0")
        values["normal_consumption"] = values.get("normal_consumption") or Decimal("0")
        values["valley_consumption"] = values.get("valley_consumption") or Decimal("0")

        template_id = values.get("usage_curve_template_id")
        if template_id and consumption_json is None:
            template = UsageCurveTemplateService.get(db, template_id)
            if template:
                hours = peak_valley_to_24h(
                    values["peak_consumption"],
                    values["high_consumption"],
                    values["normal_consumption"],
                    values["valley_consumption"],
                    template,
                    is_peak_month=False,
                )
                values["consumption_data_json"] = json.dumps(
                    {"hours": hours}, ensure_ascii=False
                )
                values["usage_curve_template_name"] = template.get("template_name")
        elif consumption_json:
            values["consumption_data_json"] = json.dumps(consumption_json, ensure_ascii=False)
    elif submit_type == 3:
        # 96-point reference / data
        if consumption_json:
            values["consumption_data_json"] = json.dumps(consumption_json, ensure_ascii=False)
    else:
        if consumption_json:
            values["consumption_data_json"] = json.dumps(consumption_json, ensure_ascii=False)

    return values


def list_inquiries(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    inquiry_status: Optional[int] = None,
    customer_name: Optional[str] = None,
    usage_month: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> dict:
    """Return paginated list of inquiries with soft-delete filter."""
    q = db.query(Inquiry).filter(Inquiry.deleted_at.is_(None))
    if inquiry_status is not None:
        q = q.filter(Inquiry.inquiry_status == inquiry_status)
    if customer_name:
        q = q.filter(Inquiry.customer_name.ilike(f"%{customer_name}%"))
    if usage_month:
        q = q.filter(Inquiry.usage_month == usage_month)
    if agent_id is not None:
        q = q.filter(Inquiry.agent_id == agent_id)
    q = q.order_by(Inquiry.created_at.desc())
    page_result = paginate_query(db, q, page, page_size)
    page_result["list"] = [_inquiry_out(item) for item in page_result["list"]]
    return page_result


def get_inquiry(db: Session, record_id: int) -> Optional[dict]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    return _inquiry_out(obj) if obj else None


def create_inquiry(db: Session, data: InquiryCreate) -> Inquiry:
    values = data.model_dump(exclude_none=True)
    values = _fill_customer_defaults(db, data, values)
    values = _prepare_consumption_data(db, data, values)

    values.setdefault("inquiry_status", STATUS_PENDING)
    values["inquiry_no"] = _generate_inquiry_no(db)

    obj = Inquiry(**values)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_inquiry(db: Session, data: InquiryUpdate) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == data.id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None

    if obj.inquiry_status not in (STATUS_PENDING, STATUS_QUOTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能修改待处理或已报价状态的询价单",
        )

    values = data.model_dump(exclude={"id"}, exclude_none=True)
    values = _fill_customer_defaults(db, data, values)
    values = _prepare_consumption_data(
        db, InquiryCreate(**data.model_dump(exclude={"id"})), values
    )

    for k, v in values.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_inquiry(db: Session, record_id: int) -> bool:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return False
    obj.deleted_at = _now()
    db.commit()
    return True


def quote_inquiry(db: Session, record_id: int, payload: QuotePayload) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态为 {_STATUS_LABELS.get(obj.inquiry_status, obj.inquiry_status)}，无法报价",
        )

    obj.price_difference = payload.price_difference
    obj.recommended_package_type = payload.recommended_package_type
    obj.quote_valid_until = payload.quote_valid_until
    obj.estimated_monthly_fee = payload.estimated_monthly_fee
    obj.estimated_savings = payload.estimated_savings
    obj.savings_rate = payload.savings_rate
    if payload.remark is not None:
        obj.remark = payload.remark
    obj.quoted_at = _now()
    obj.inquiry_status = STATUS_QUOTED
    db.commit()
    db.refresh(obj)
    return obj


def accept_inquiry(db: Session, record_id: int) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_QUOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能接受已报价状态的询价单",
        )
    obj.inquiry_status = STATUS_ACCEPTED
    obj.customer_confirm_time = _now()
    db.commit()
    db.refresh(obj)
    return obj


def reject_inquiry(db: Session, record_id: int, reason: Optional[str] = None) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_QUOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能拒绝已报价状态的询价单",
        )
    obj.inquiry_status = STATUS_REJECTED
    obj.reject_reason = reason
    db.commit()
    db.refresh(obj)
    return obj


def cooperate_inquiry(
    db: Session,
    record_id: int,
    cooperation_start_date: Optional[date] = None,
    cooperation_end_date: Optional[date] = None,
) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能将已接受状态的询价单转为合作",
        )
    obj.inquiry_status = STATUS_COOPERATED
    obj.cooperation_start_date = cooperation_start_date
    obj.cooperation_end_date = cooperation_end_date
    obj.admin_confirm_time = _now()
    db.commit()
    db.refresh(obj)
    return obj


def terminate_inquiry(db: Session, record_id: int, terminate_date: Optional[date] = None) -> Optional[Inquiry]:
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_COOPERATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能终止已合作状态的询价单",
        )
    obj.inquiry_status = STATUS_REJECTED
    obj.terminate_date = terminate_date or date.today()
    db.commit()
    db.refresh(obj)
    return obj


def get_statistics(db: Session) -> dict:
    """Return counts by status."""
    q = db.query(Inquiry).filter(Inquiry.deleted_at.is_(None))
    total = q.count()
    counts = {
        STATUS_PENDING: 0,
        STATUS_QUOTED: 0,
        STATUS_ACCEPTED: 0,
        STATUS_REJECTED: 0,
        STATUS_EXPIRED: 0,
        STATUS_COOPERATED: 0,
    }
    for status_value, count in (
        db.query(Inquiry.inquiry_status, func.count(Inquiry.id))
        .filter(Inquiry.deleted_at.is_(None))
        .group_by(Inquiry.inquiry_status)
        .all()
    ):
        if status_value in counts:
            counts[status_value] = count

    return {
        "total": total,
        "pending": counts[STATUS_PENDING],
        "quoted": counts[STATUS_QUOTED],
        "accepted": counts[STATUS_ACCEPTED],
        "rejected": counts[STATUS_REJECTED],
        "expired": counts[STATUS_EXPIRED],
        "cooperated": counts[STATUS_COOPERATED],
    }


def export_inquiries(
    db: Session,
    inquiry_status: Optional[int] = None,
    customer_name: Optional[str] = None,
    usage_month: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> bytes:
    """Generate Excel export of inquiries."""
    from openpyxl import Workbook

    q = db.query(Inquiry).filter(Inquiry.deleted_at.is_(None))
    if inquiry_status is not None:
        q = q.filter(Inquiry.inquiry_status == inquiry_status)
    if customer_name:
        q = q.filter(Inquiry.customer_name.ilike(f"%{customer_name}%"))
    if usage_month:
        q = q.filter(Inquiry.usage_month == usage_month)
    if agent_id is not None:
        q = q.filter(Inquiry.agent_id == agent_id)
    items = q.order_by(Inquiry.created_at.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "询价单"
    headers = [
        "询价单号",
        "客户名称",
        "联系人",
        "联系电话",
        "电压等级",
        "用电月份",
        "预计月用电量",
        "用电地址",
        "行业类型",
        "数据提交方式",
        "状态",
        "推荐套餐",
        "价差",
        "预计月电费",
        "预计节省",
        "节省率",
        "创建时间",
    ]
    ws.append(headers)

    for item in items:
        status_label = _STATUS_LABELS.get(item.inquiry_status, item.inquiry_status)
        package_label = {1: "一口价", 2: "分时价"}.get(item.recommended_package_type, "")
        submit_label = {1: "24h", 2: "峰谷", 3: "96点"}.get(item.data_submit_type, "")
        ws.append([
            item.inquiry_no,
            item.customer_name,
            item.contact_person,
            item.contact_phone,
            item.voltage_level,
            item.usage_month,
            item.estimated_monthly_consumption,
            item.usage_address,
            item.industry_type,
            submit_label,
            status_label,
            package_label,
            item.price_difference,
            item.estimated_monthly_fee,
            item.estimated_savings,
            item.savings_rate,
            item.created_at,
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def calculate_price(db: Session, payload: CalculatePricePayload) -> dict:
    """Estimate monthly fee and savings using simplified formulas."""
    estimated_consumption = payload.estimated_consumption
    price_difference = payload.price_difference
    grid_price = payload.grid_price or Decimal("0.6")

    if payload.package_type == 1:
        # 一口价: consumption * (grid_price + price_difference)
        estimated_monthly_fee = estimated_consumption * (grid_price + price_difference)
    elif payload.package_type == 2:
        # 分时价: average wholesale price + price_difference per hour
        wholesale_prices = payload.wholesale_prices
        if wholesale_prices:
            avg_wholesale = sum(wholesale_prices, Decimal("0")) / Decimal("24")
        else:
            avg_wholesale = grid_price
        estimated_monthly_fee = estimated_consumption * (avg_wholesale + price_difference)
    else:
        estimated_monthly_fee = estimated_consumption * (grid_price + price_difference)

    original_grid_fee = estimated_consumption * grid_price
    estimated_savings = original_grid_fee - estimated_monthly_fee
    if original_grid_fee != 0:
        savings_rate = (estimated_savings / original_grid_fee).quantize(Decimal("0.0001"))
    else:
        savings_rate = Decimal("0")

    return {
        "estimated_monthly_fee": estimated_monthly_fee.quantize(Decimal("0.0001")),
        "estimated_savings": estimated_savings.quantize(Decimal("0.0001")),
        "savings_rate": savings_rate,
        "remark": "简化计算，Phase 2/3 细化",
    }


def upload_consumption_data(
    db: Session, record_id: int, file: UploadFile
) -> Optional[dict]:
    """Store uploaded file reference in consumption_data_json."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None

    reference = {
        "file_name": file.filename,
        "content_type": file.content_type,
        "uploaded_at": _now().isoformat(),
    }
    existing = _parse_json(obj.consumption_data_json) or {}
    if isinstance(existing, dict):
        existing.setdefault("uploads", [])
        existing["uploads"].append(reference)
    else:
        existing = {"uploads": [reference]}
    obj.consumption_data_json = json.dumps(existing, ensure_ascii=False)
    db.commit()
    db.refresh(obj)
    return {"file_name": file.filename, "reference": reference}


def get_consumption_data(db: Session, record_id: int) -> Optional[dict]:
    """Return parsed consumption_data_json."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    return _parse_json(obj.consumption_data_json) or {}


# ===========================================================================
# Task #45 — Missing inquiry endpoints
# ===========================================================================


def _extract_hourly_consumption(obj: Inquiry) -> list[Decimal]:
    """Extract 24h consumption values from inquiry's consumption_data_json."""
    data = _parse_json(obj.consumption_data_json)
    if not data:
        return []
    hours = data.get("hours") if isinstance(data, dict) else None
    if hours and isinstance(hours, list) and len(hours) >= 24:
        return [Decimal(str(h)) if h is not None else Decimal("0") for h in hours[:24]]
    return []


def generate_inquiry_no(db: Session) -> str:
    """GET /generate-no — generate an inquiry number without creating."""
    return _generate_inquiry_no(db)


def list_all(
    db: Session,
    inquiry_status: Optional[int] = None,
    customer_name: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> list[dict]:
    """GET /list — list without pagination."""
    q = db.query(Inquiry).filter(Inquiry.deleted_at.is_(None))
    if inquiry_status is not None:
        q = q.filter(Inquiry.inquiry_status == inquiry_status)
    if customer_name:
        q = q.filter(Inquiry.customer_name.ilike(f"%{customer_name}%"))
    if agent_id is not None:
        q = q.filter(Inquiry.agent_id == agent_id)
    items = q.order_by(Inquiry.created_at.desc()).all()
    return [_inquiry_out(item) for item in items]


def simple_list(db: Session) -> list[dict]:
    """GET /simple-list — minimal option list (id, inquiry_no, customer_name, status)."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "inquiry_no": item.inquiry_no,
            "customer_name": item.customer_name,
            "inquiry_status": item.inquiry_status,
        }
        for item in items
    ]


def list_by_agent(db: Session, agent_id: int) -> list[dict]:
    """GET /by-agent/{agentId}."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.agent_id == agent_id, Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_pending(db: Session) -> list[dict]:
    """GET /pending — status=PENDING."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.inquiry_status == STATUS_PENDING, Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_pending_quotes(db: Session) -> list[dict]:
    """GET /pending-quote-list — status=PENDING or QUOTED."""
    items = (
        db.query(Inquiry)
        .filter(
            Inquiry.inquiry_status.in_([STATUS_PENDING, STATUS_QUOTED]),
            Inquiry.deleted_at.is_(None),
        )
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_expired(db: Session) -> list[dict]:
    """GET /expired — status=EXPIRED."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.inquiry_status == STATUS_EXPIRED, Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_by_customer(db: Session, customer_name: str) -> list[dict]:
    """GET /list-by-customer."""
    items = (
        db.query(Inquiry)
        .filter(
            Inquiry.customer_name.ilike(f"%{customer_name}%"),
            Inquiry.deleted_at.is_(None),
        )
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_by_status(db: Session, inquiry_status: int) -> list[dict]:
    """GET /list-by-status."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.inquiry_status == inquiry_status, Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def count_by_status(db: Session) -> dict:
    """GET /count-by-status."""
    rows = (
        db.query(Inquiry.inquiry_status, func.count(Inquiry.id))
        .filter(Inquiry.deleted_at.is_(None))
        .group_by(Inquiry.inquiry_status)
        .all()
    )
    return {str(status_val): count for status_val, count in rows}


def list_by_time_range(
    db: Session, start_date: str, end_date: str
) -> list[dict]:
    """GET /list-by-time-range."""
    items = (
        db.query(Inquiry)
        .filter(
            Inquiry.deleted_at.is_(None),
            Inquiry.created_at >= start_date,
            Inquiry.created_at <= end_date,
        )
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_by_month(db: Session, usage_month: str) -> list[dict]:
    """GET /list-by-month."""
    items = (
        db.query(Inquiry)
        .filter(Inquiry.usage_month == usage_month, Inquiry.deleted_at.is_(None))
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def list_by_year(db: Session, year: str) -> list[dict]:
    """GET /list-by-year."""
    items = (
        db.query(Inquiry)
        .filter(
            Inquiry.usage_month.like(f"{year}-%"),
            Inquiry.deleted_at.is_(None),
        )
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(item) for item in items]


def batch_update_status(db: Session, ids: list[int], new_status: int) -> int:
    """PUT /batch-update-status — bulk status change."""
    count = (
        db.query(Inquiry)
        .filter(Inquiry.id.in_(ids), Inquiry.deleted_at.is_(None))
        .update({Inquiry.inquiry_status: new_status}, synchronize_session=False)
    )
    db.commit()
    return count


def submit_inquiry(db: Session, record_id: int) -> Optional[Inquiry]:
    """POST /submit — transition from draft/pending to pending (for quoting)."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    obj.inquiry_status = STATUS_PENDING
    db.commit()
    db.refresh(obj)
    return obj


def reject_inquiry_cooperation(
    db: Session, record_id: int, reason: Optional[str] = None
) -> Optional[Inquiry]:
    """POST /reject-inquiry/{id} — reject the inquiry itself (status 1→4)."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能拒绝待处理状态的询价单",
        )
    obj.inquiry_status = STATUS_REJECTED
    obj.reject_reason = reason
    db.commit()
    db.refresh(obj)
    return obj


def accept_quote_by_customer(db: Session, record_id: int) -> Optional[Inquiry]:
    """POST /accept-quote-by-customer/{id} — customer accepts the quote (status 2→3)."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_QUOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="客户只能接受已报价状态的询价单",
        )
    if obj.quote_valid_until and obj.quote_valid_until < _now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报价已过期",
        )
    obj.inquiry_status = STATUS_ACCEPTED
    obj.customer_confirm_time = _now()
    db.commit()
    db.refresh(obj)
    return obj


def approve_quote(db: Session, record_id: int) -> Optional[Inquiry]:
    """POST /approve-quote/{id} — admin approves quote (status 2→3)."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_QUOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能审核已报价状态的询价单",
        )
    obj.inquiry_status = STATUS_ACCEPTED
    obj.admin_confirm_time = _now()
    db.commit()
    db.refresh(obj)
    return obj


def reject_quote_admin(db: Session, record_id: int, reason: Optional[str] = None) -> Optional[Inquiry]:
    """POST /reject-quote/{id} — admin rejects quote (status 2→4)."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_QUOTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能驳回已报价状态的询价单",
        )
    obj.inquiry_status = STATUS_REJECTED
    obj.reject_reason = reason
    db.commit()
    db.refresh(obj)
    return obj


def confirm_cooperation(
    db: Session,
    record_id: int,
    cooperation_start_date: Optional[date] = None,
    cooperation_end_date: Optional[date] = None,
) -> Optional[Inquiry]:
    """POST /confirm-cooperation/{id} — status 3→6, create customer account side-effect."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能确认已接受状态的询价单",
        )
    obj.inquiry_status = STATUS_COOPERATED
    obj.cooperation_start_date = cooperation_start_date
    obj.cooperation_end_date = cooperation_end_date
    obj.admin_confirm_time = _now()

    # Side effect: create CustomerAccount (failure is logged, not rolled back)
    try:
        _create_customer_account_from_inquiry(db, obj)
    except Exception as exc:
        logger.warning("Failed to create customer account from inquiry %s: %s", record_id, exc)

    db.commit()
    db.refresh(obj)
    return obj


def _create_customer_account_from_inquiry(db: Session, inquiry: Inquiry) -> None:
    """Create a customer account from a confirmed inquiry (mirrors Java side-effect)."""
    existing = (
        db.query(CustomerAccount)
        .filter(
            CustomerAccount.customer_name == inquiry.customer_name,
            CustomerAccount.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        return

    account = CustomerAccount(
        customer_name=inquiry.customer_name,
        agent_id=inquiry.agent_id,
        agent_name=inquiry.agent_name,
        voltage_level=inquiry.voltage_level,
        customer_type=inquiry.customer_type,
        package_type=inquiry.recommended_package_type,
        price_difference=inquiry.price_difference,
        contact_person=inquiry.contact_person,
        contact_phone=inquiry.contact_phone,
        industry_type=inquiry.industry_type,
        usage_address=inquiry.usage_address,
        customer_status=3,  # 待签约
        region=inquiry.region,
    )
    db.add(account)


def terminate_cooperation(
    db: Session, record_id: int, terminate_date: Optional[date] = None
) -> Optional[Inquiry]:
    """POST /terminate-cooperation/{id} — set terminate date on cooperated inquiry."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    if obj.inquiry_status != STATUS_COOPERATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能终止已合作状态的询价单",
        )
    # terminate_date must be >= first day of next month
    today = date.today()
    first_next_month = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    obj.terminate_date = terminate_date or first_next_month
    db.commit()
    db.refresh(obj)
    return obj


def mark_expired(db: Session, record_id: int) -> Optional[Inquiry]:
    """POST /mark-expired/{id} — mark inquiry as expired."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    obj.inquiry_status = STATUS_EXPIRED
    db.commit()
    db.refresh(obj)
    return obj


def batch_process_expired(db: Session) -> int:
    """POST /batch-process-expired — mark all quotes past validity as expired."""
    now = _now()
    count = (
        db.query(Inquiry)
        .filter(
            Inquiry.inquiry_status == STATUS_QUOTED,
            Inquiry.quote_valid_until < now,
            Inquiry.deleted_at.is_(None),
        )
        .update({Inquiry.inquiry_status: STATUS_EXPIRED}, synchronize_session=False)
    )
    db.commit()
    return count


def get_consumption_summary(db: Session, record_id: int) -> Optional[dict]:
    """GET /consumption-summary/{id} — aggregated consumption stats."""
    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        return None
    hours = _extract_hourly_consumption(obj)
    if not hours:
        return {
            "totalConsumption": Decimal("0"),
            "peakConsumption": obj.peak_consumption or Decimal("0"),
            "highConsumption": obj.high_consumption or Decimal("0"),
            "normalConsumption": obj.normal_consumption or Decimal("0"),
            "valleyConsumption": obj.valley_consumption or Decimal("0"),
            "hourlyData": [],
        }
    return {
        "totalConsumption": sum(hours, Decimal("0")),
        "peakConsumption": obj.peak_consumption or Decimal("0"),
        "highConsumption": obj.high_consumption or Decimal("0"),
        "normalConsumption": obj.normal_consumption or Decimal("0"),
        "valleyConsumption": obj.valley_consumption or Decimal("0"),
        "hourlyData": [{"hour": h, "consumption": float(hours[h])} for h in range(24)],
    }


# ─── Pricing engine integration ────────────────────────────────────────────

def calculate_quote_auto(db: Session, record_id: int) -> dict:
    """GET /calculate-quote — basic auto-quote using the pricing engine."""
    from app.services import pricing_engine

    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="询价单不存在")

    hourly = _extract_hourly_consumption(obj)
    if not hourly:
        raise HTTPException(status_code=400, detail="询价单无用电量数据")

    usage_month = obj.usage_month or _now().strftime("%Y-%m")
    rec = pricing_engine.calculate_optimal_pricing(db, record_id, usage_month, hourly)
    rec_dict = pricing_engine.recommendation_to_dict(rec)

    # Build quote response
    primary = rec.timed_package_result if rec.recommended_package_type == 2 else rec.flat_rate_package_result
    return {
        "inquiryId": record_id,
        "recommendedPackageType": rec.recommended_package_type,
        "priceDifference": rec_dict["optimalPriceDifference"],
        "estimatedMonthlyFee": rec_dict["expectedMonthlyFee"],
        "estimatedSavings": rec_dict["expectedSavings"],
        "savingsRate": rec_dict["expectedSavingsRate"],
        "quoteValidUntil": (_now().replace(day=_now().day + 7)).isoformat() if _now().day <= 21 else None,
        "quoteRemark": f"{rec.recommendation_reason}\n{rec.price_difference_explanation}\n{rec.risk_assessment}",
    }


def calculate_advanced_quote(db: Session, record_id: int) -> dict:
    """GET /calculate-advanced-quote — full detail with both packages."""
    from app.services import pricing_engine

    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="询价单不存在")

    hourly = _extract_hourly_consumption(obj)
    if not hourly:
        raise HTTPException(status_code=400, detail="询价单无用电量数据")

    usage_month = obj.usage_month or _now().strftime("%Y-%m")
    rec = pricing_engine.calculate_optimal_pricing(db, record_id, usage_month, hourly)
    rec_dict = pricing_engine.recommendation_to_dict(rec)

    package_name = {1: "一口价套餐", 2: "分时价套餐"}.get(rec.recommended_package_type, "未确定")
    rec_dict["customerName"] = obj.customer_name
    rec_dict["usageMonth"] = usage_month
    rec_dict["recommendedPackageTypeName"] = package_name
    rec_dict["dataSourceDescription"] = f"基于{usage_month}月的国网价格、批发价格、市场分摊价格等真实数据计算"
    rec_dict["algorithmVersion"] = "高级动态报价引擎 v2.0 (Python)"

    # Package comparison advice
    timed = rec.timed_package_result
    flat = rec.flat_rate_package_result
    if timed and flat and timed.successful and flat.successful:
        savings_diff = timed.savings - flat.savings
        profit_diff = timed.profit - flat.profit
        advice = (
            f"套餐对比分析：分时比分时套餐省钱差异{savings_diff}元，"
            f"利润差异{profit_diff}元。"
        )
        if savings_diff > 0:
            advice += "建议：优先推荐分时价套餐"
        else:
            advice += "建议：优先推荐一口价套餐"
        rec_dict["packageComparisonAdvice"] = advice

    return rec_dict


def calculate_dynamic_pricing(
    db: Session, record_id: int, price_difference: Decimal
) -> dict:
    """GET /calculate-dynamic-pricing/{id} — what-if calculator with user-supplied diff."""
    from app.services import pricing_engine

    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="询价单不存在")

    hourly = _extract_hourly_consumption(obj)
    if not hourly:
        raise HTTPException(status_code=400, detail="询价单无用电量数据")

    usage_month = obj.usage_month or _now().strftime("%Y-%m")

    timed = pricing_engine.calculate_timed_package_pricing(db, usage_month, price_difference, hourly)
    flat = pricing_engine.calculate_flat_rate_package_pricing(db, usage_month, price_difference, hourly)

    def _pkg_dict(r: pricing_engine.PackagePricingResult) -> dict:
        if not r.successful:
            return {"available": False, "errorMessage": r.error_message}
        return {
            "available": True,
            "averagePrice": float(r.average_price),
            "totalFee": float(r.total_electricity_fee),
            "savings": float(r.savings),
            "savingsRate": float(r.savings_rate),
            "profit": float(r.profit),
            "profitRate": float(r.profit_rate),
            "gridTotalFee": float(r.grid_total_fee),
        }

    return {
        "timed": _pkg_dict(timed),
        "flatRate": _pkg_dict(flat),
        "priceDifference": float(price_difference),
        "totalConsumption": float(timed.total_consumption) if timed.successful else 0,
    }


def export_quote_result(db: Session, record_id: int) -> bytes:
    """GET /export-quote-result/{id} — Excel export of detailed quote."""
    from openpyxl import Workbook

    obj = (
        db.query(Inquiry)
        .filter(Inquiry.id == record_id, Inquiry.deleted_at.is_(None))
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="询价单不存在")

    hourly = _extract_hourly_consumption(obj)
    usage_month = obj.usage_month or ""

    wb = Workbook()
    ws = wb.active
    ws.title = "报价详情"

    # Header info
    ws.append(["询价单号", obj.inquiry_no])
    ws.append(["客户名称", obj.customer_name])
    ws.append(["用电月份", usage_month])
    ws.append(["推荐套餐", {1: "一口价", 2: "分时价"}.get(obj.recommended_package_type, "")])
    ws.append(["价差", float(obj.price_difference) if obj.price_difference else ""])
    ws.append(["预计月电费", float(obj.estimated_monthly_fee) if obj.estimated_monthly_fee else ""])
    ws.append(["预计节省", float(obj.estimated_savings) if obj.estimated_savings else ""])
    ws.append(["节省率", f"{float(obj.savings_rate)}%" if obj.savings_rate else ""])
    ws.append([])

    # 24-hour detail
    ws.append(["小时", "用电量(kWh)", "客户电价", "国网电价", "批发价", "客户电费", "国网电费", "批发成本"])
    for hour in range(24):
        consumption = float(hourly[hour]) if hour < len(hourly) else 0
        ws.append([hour, consumption, "", "", "", "", "", ""])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
