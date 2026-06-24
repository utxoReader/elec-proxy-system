"""Usage curve template business logic."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.crud.base import paginate_query
from app.models.usage_curve import UsageCurveTemplate
from app.schemas.usage_curve_template import (
    UsageCurveTemplateCreate,
    UsageCurveTemplateUpdate,
)

PEAK_MONTHS = {1, 7, 8, 12}


def _template_out(obj: UsageCurveTemplate) -> dict:
    return {
        "id": obj.id,
        "template_name": obj.template_name,
        "description": obj.description,
        "template_type": obj.template_type,
        "industry": obj.industry,
        "image_url": obj.image_url,
        **{f"hour_{h:02d}_ratio": getattr(obj, f"hour_{h:02d}_ratio") for h in range(24)},
        **{f"hour_{h:02d}_peak_ratio": getattr(obj, f"hour_{h:02d}_peak_ratio") for h in range(24)},
        "status": obj.status,
        "is_default": obj.is_default,
        "sort": obj.sort,
        "region": obj.region,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def _extract_ratios(obj: UsageCurveTemplate, peak: bool = False) -> list[Optional[Decimal]]:
    suffix = "_peak_ratio" if peak else "_ratio"
    return [getattr(obj, f"hour_{h:02d}{suffix}") for h in range(24)]


def _is_peak_hour(hour: int) -> bool:
    """Check if hour falls in peak (尖峰) window (18:00-19:00)."""
    return hour in (18, 19)


class UsageCurveTemplateService:
    """CRUD + business logic service for UsageCurveTemplate."""

    # ------------------------------------------------------------------
    # Basic CRUD (existing)
    # ------------------------------------------------------------------

    @staticmethod
    def list_page(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        template_name: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[int] = None,
    ) -> dict:
        q = db.query(UsageCurveTemplate).filter(UsageCurveTemplate.deleted_at.is_(None))
        if template_name:
            q = q.filter(UsageCurveTemplate.template_name.ilike(f"%{template_name}%"))
        if industry:
            q = q.filter(UsageCurveTemplate.industry == industry)
        if status is not None:
            q = q.filter(UsageCurveTemplate.status == status)
        q = q.order_by(UsageCurveTemplate.sort.asc(), UsageCurveTemplate.created_at.desc())
        page_result = paginate_query(db, q, page, page_size)
        page_result["list"] = [_template_out(item) for item in page_result["list"]]
        return page_result

    @staticmethod
    def get(db: Session, record_id: int) -> Optional[dict]:
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == record_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        return _template_out(obj) if obj else None

    @staticmethod
    def create(db: Session, data: UsageCurveTemplateCreate) -> UsageCurveTemplate:
        obj = UsageCurveTemplate(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, data: UsageCurveTemplateUpdate) -> Optional[UsageCurveTemplate]:
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == data.id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        if not obj:
            return None
        for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, record_id: int) -> bool:
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == record_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        if not obj:
            return False
        obj.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True

    # ------------------------------------------------------------------
    # New endpoints (task #47)
    # ------------------------------------------------------------------

    @staticmethod
    def list_enabled(db: Session) -> list[dict]:
        """GET /enabled — all enabled (status=1) templates."""
        items = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.status == 1,
            )
            .order_by(UsageCurveTemplate.sort.asc())
            .all()
        )
        return [_template_out(item) for item in items]

    @staticmethod
    def get_by_type(db: Session, template_type: int) -> list[dict]:
        """GET /by-type — templates filtered by template_type."""
        items = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.template_type == template_type,
            )
            .order_by(UsageCurveTemplate.sort.asc())
            .all()
        )
        return [_template_out(item) for item in items]

    @staticmethod
    def get_default(db: Session) -> Optional[dict]:
        """GET /default — the default template (is_default=1)."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.is_default == 1,
            )
            .first()
        )
        if not obj:
            # fallback: first enabled template
            obj = (
                db.query(UsageCurveTemplate)
                .filter(
                    UsageCurveTemplate.deleted_at.is_(None),
                    UsageCurveTemplate.status == 1,
                )
                .order_by(UsageCurveTemplate.sort.asc())
                .first()
            )
        return _template_out(obj) if obj else None

    @staticmethod
    def set_default(db: Session, template_id: int) -> bool:
        """PUT /set-default — make template_id the sole default."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == template_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        if not obj:
            return False
        # clear all defaults
        db.query(UsageCurveTemplate).filter(
            UsageCurveTemplate.is_default == 1,
            UsageCurveTemplate.deleted_at.is_(None),
        ).update({UsageCurveTemplate.is_default: 0}, synchronize_session=False)
        # set new default
        obj.is_default = 1
        db.commit()
        return True

    @staticmethod
    def update_status(db: Session, template_id: int, new_status: int) -> bool:
        """PUT /update-status — change enabled/disabled status."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == template_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        if not obj:
            return False
        obj.status = new_status
        db.commit()
        return True

    @staticmethod
    def get_hourly_ratios(db: Session, template_id: int) -> Optional[list[Optional[Decimal]]]:
        """GET /hourly-ratios — extract 24h normal ratios as a plain list."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == template_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        return _extract_ratios(obj, peak=False) if obj else None

    @staticmethod
    def get_hourly_ratios_by_type(db: Session, template_type: int) -> list[dict]:
        """GET /hourly-ratios-by-type — 24h ratios for all templates of a type."""
        items = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.template_type == template_type,
            )
            .order_by(UsageCurveTemplate.sort.asc())
            .all()
        )
        return [
            {
                "templateId": item.id,
                "templateName": item.template_name,
                "hourlyRatios": _extract_ratios(item, peak=False),
            }
            for item in items
        ]

    @staticmethod
    def validate_ratios(ratios: list[Optional[Decimal]]) -> dict:
        """POST /validate-ratios — check whether 24 ratios sum to ~1.0 (±0.05)."""
        valid_values = [r for r in ratios if r is not None]
        if len(valid_values) < 24:
            return {
                "valid": False,
                "message": f"需要24个小时的比例值，当前只有 {len(valid_values)} 个",
                "sum": None,
            }
        total = sum(valid_values)
        tolerance = Decimal("0.05")
        is_valid = abs(total - Decimal("1.0")) <= tolerance or abs(total - Decimal("100.0")) <= tolerance * 100
        return {
            "valid": is_valid,
            "message": "比例验证通过" if is_valid else f"比例之和为 {total}，应为 1.0（±0.05）",
            "sum": float(total),
        }

    @staticmethod
    def get_hourly_peak_ratios(db: Session, template_id: int) -> Optional[list[Optional[Decimal]]]:
        """GET /hourly-peak-ratios — 24h peak-month ratios."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == template_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        return _extract_ratios(obj, peak=True) if obj else None

    @staticmethod
    def get_hourly_peak_ratios_by_type(db: Session, template_type: int) -> list[dict]:
        """GET /hourly-peak-ratios-by-type — peak ratios for all templates of a type."""
        items = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.template_type == template_type,
            )
            .order_by(UsageCurveTemplate.sort.asc())
            .all()
        )
        return [
            {
                "templateId": item.id,
                "templateName": item.template_name,
                "hourlyPeakRatios": _extract_ratios(item, peak=True),
            }
            for item in items
        ]

    @staticmethod
    def get_hourly_ratios_with_peak(
        db: Session, template_id: int, is_peak_month: bool = False
    ) -> Optional[dict]:
        """GET /hourly-ratios-with-peak — ratios + per-hour isPeak flag."""
        obj = (
            db.query(UsageCurveTemplate)
            .filter(UsageCurveTemplate.id == template_id, UsageCurveTemplate.deleted_at.is_(None))
            .first()
        )
        if not obj:
            return None
        normal = _extract_ratios(obj, peak=False)
        peak = _extract_ratios(obj, peak=True)
        ratios = peak if is_peak_month else normal
        return {
            "templateId": obj.id,
            "templateName": obj.template_name,
            "isPeakMonth": is_peak_month,
            "hourlyRatios": [
                {
                    "hour": h,
                    "ratio": ratios[h],
                    "isPeak": is_peak_month and _is_peak_hour(h),
                }
                for h in range(24)
            ],
        }

    @staticmethod
    def get_hourly_ratios_by_type_with_peak(
        db: Session, template_type: int, is_peak_month: bool = False
    ) -> list[dict]:
        """GET /hourly-ratios-by-type-with-peak — same as above but for all templates of a type."""
        items = (
            db.query(UsageCurveTemplate)
            .filter(
                UsageCurveTemplate.deleted_at.is_(None),
                UsageCurveTemplate.template_type == template_type,
            )
            .order_by(UsageCurveTemplate.sort.asc())
            .all()
        )
        results: list[dict] = []
        for obj in items:
            normal = _extract_ratios(obj, peak=False)
            peak = _extract_ratios(obj, peak=True)
            ratios = peak if is_peak_month else normal
            results.append({
                "templateId": obj.id,
                "templateName": obj.template_name,
                "isPeakMonth": is_peak_month,
                "hourlyRatios": [
                    {
                        "hour": h,
                        "ratio": ratios[h],
                        "isPeak": is_peak_month and _is_peak_hour(h),
                    }
                    for h in range(24)
                ],
            })
        return results
