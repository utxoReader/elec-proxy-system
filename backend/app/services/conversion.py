"""Data conversion utilities between curve formats."""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.consumption import CustomerDailyConsumption, Point96Data
from app.models.usage_curve import UsageCurveTemplate

if TYPE_CHECKING:
    pass


def _to_decimal(value) -> Decimal:
    """Normalize a value to Decimal, treating None as 0."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def point96_to_24h(point96_data: Point96Data) -> dict:
    """Aggregate 96 x 15-min points into 24 hourly totals.

    The Point96Data object is expected to expose attributes following the
    naming pattern ``pHH15``, ``pHH30``, ``pHH45`` and ``p(HH+1)00`` (or
    equivalent label-based points via ``points``). This implementation
    aggregates any matching attributes that exist on the object so it works
    for both the abbreviated model and the full 96-point migration.

    Returns:
        Dict with keys ``hour_00`` .. ``hour_23`` and Decimal values.
    """
    hours = {f"hour_{h:02d}": Decimal("0") for h in range(24)}

    # Prefer explicit points dict if available, otherwise scan attributes / keys.
    points_source = getattr(point96_data, "points", None) or {}
    attr_points = {}
    if not points_source:
        if isinstance(point96_data, Point96Data):
            for name in dir(point96_data):
                if name.startswith("p") and len(name) == 5 and name[1:].isdigit():
                    attr_points[name] = getattr(point96_data, name)
        elif isinstance(point96_data, dict):
            for name, value in point96_data.items():
                if name.startswith("p") and len(name) == 5 and name[1:].isdigit():
                    attr_points[name] = value
        points_source = attr_points

    for label, value in points_source.items():
        if value is None:
            continue
        # label may be "00:15" or an attribute name like "p0015".
        # 96-point convention: pHHMM belongs to hour HH except HH:00,
        # which closes the previous hour (e.g. 01:00 -> hour_00).
        if ":" in str(label):
            hour_str, minute_str = str(label).split(":")
            hour, minute = int(hour_str), int(minute_str)
        else:
            hour = int(str(label)[1:3])
            minute = int(str(label)[3:5])
        if minute == 0:
            hour = (hour - 1) % 24
        key = f"hour_{hour:02d}"
        hours[key] = hours.get(key, Decimal("0")) + _to_decimal(value)

    return {k: v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) for k, v in hours.items()}


def peak_valley_to_24h(
    peak: Decimal,
    high: Decimal,
    normal: Decimal,
    valley: Decimal,
    template: UsageCurveTemplate,
    is_peak_month: bool,
) -> dict:
    """Split peak/high/normal/valley totals into 24h using template ratios.

    Args:
        peak: Total peak-period consumption.
        high: Total high-period consumption.
        normal: Total normal-period consumption.
        valley: Total valley-period consumption.
        template: UsageCurveTemplate with hour_XX_ratio / hour_XX_peak_ratio.
        is_peak_month: When True, use peak-month ratios.

    Returns:
        Dict with keys ``hour_00`` .. ``hour_23``.
    """
    suffix = "_peak_ratio" if is_peak_month else "_ratio"
    ratios = {}
    for h in range(24):
        attr = f"hour_{h:02d}{suffix}"
        if isinstance(template, UsageCurveTemplate):
            value = getattr(template, attr, None)
        elif isinstance(template, dict):
            value = template.get(attr)
        else:
            value = None
        ratios[f"hour_{h:02d}"] = _to_decimal(value)

    total_ratio = sum(ratios.values())
    if total_ratio == 0:
        # No template ratios: return equal split of total consumption.
        total = _to_decimal(peak) + _to_decimal(high) + _to_decimal(normal) + _to_decimal(valley)
        per_hour = (total / Decimal("24")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return {f"hour_{h:02d}": per_hour for h in range(24)}

    # Simplified allocation: scale the grand total by each hour's ratio.
    # This keeps the function self-contained; time-period mapping is left to
    # callers/template design.
    grand_total = _to_decimal(peak) + _to_decimal(high) + _to_decimal(normal) + _to_decimal(valley)
    result = {}
    for h in range(24):
        key = f"hour_{h:02d}"
        value = (grand_total * ratios[key] / total_ratio).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        result[key] = value
    return result


def fill_missing_daily_data(
    db: Session,
    customer_account_id: int,
    month: str,
) -> dict:
    """Placeholder: find missing dates in the month and fill with averages.

    Returns:
        Summary dict with filled_count and average_total.
    """
    from sqlalchemy import func

    q = db.query(CustomerDailyConsumption).filter(
        CustomerDailyConsumption.customer_account_id == customer_account_id,
        CustomerDailyConsumption.data_month == month,
        CustomerDailyConsumption.deleted_at.is_(None),
    )
    existing = q.all()
    if not existing:
        return {"filled_count": 0, "average_total": None, "message": "No existing data to average"}

    avg_total = (
        db.query(func.avg(CustomerDailyConsumption.total_consumption))
        .filter(
            CustomerDailyConsumption.customer_account_id == customer_account_id,
            CustomerDailyConsumption.data_month == month,
            CustomerDailyConsumption.deleted_at.is_(None),
        )
        .scalar()
    )
    avg_total = _to_decimal(avg_total)

    # Determine month days (simple YYYY-MM parsing).
    year, mon = int(month[:4]), int(month[5:7])
    from calendar import monthrange

    _, last_day = monthrange(year, mon)
    existing_dates = {row.data_date for row in existing if row.data_date}
    filled = 0
    for day in range(1, last_day + 1):
        d = date(year, mon, day)
        if d in existing_dates:
            continue
        row = CustomerDailyConsumption(
            customer_account_id=customer_account_id,
            data_date=d,
            data_month=month,
            total_consumption=avg_total,
        )
        db.add(row)
        filled += 1
    if filled:
        db.commit()
    return {
        "filled_count": filled,
        "average_total": avg_total.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
    }


def copy_daily_data(
    db: Session,
    source_customer_id: int,
    target_customer_id: int,
    month: str,
) -> dict:
    """Copy all daily consumption rows from source customer to target customer.

    The copied rows are created with the target customer id/name cleared so
    callers can fill them in afterwards.

    Returns:
        Summary dict with copied_count.
    """
    source_rows = (
        db.query(CustomerDailyConsumption)
        .filter(
            CustomerDailyConsumption.customer_account_id == source_customer_id,
            CustomerDailyConsumption.data_month == month,
            CustomerDailyConsumption.deleted_at.is_(None),
        )
        .all()
    )

    copied = 0
    for src in source_rows:
        data = {}
        for h in range(24):
            key = f"hour_{h:02d}"
            data[key] = getattr(src, key)
        new_row = CustomerDailyConsumption(
            customer_account_id=target_customer_id,
            inquiry_id=src.inquiry_id,
            data_date=src.data_date,
            data_month=src.data_month,
            total_consumption=src.total_consumption,
            peak_consumption=src.peak_consumption,
            high_consumption=src.high_consumption,
            normal_consumption=src.normal_consumption,
            valley_consumption=src.valley_consumption,
            data_type=src.data_type,
            data_source=src.data_source,
            package_type=src.package_type,
            price_difference=src.price_difference,
            remarks=src.remarks,
            commission_status=src.commission_status,
            data_locked=False,
            **data,
        )
        db.add(new_row)
        copied += 1
    if copied:
        db.commit()
    return {"copied_count": copied}
