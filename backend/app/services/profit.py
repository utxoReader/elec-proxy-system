"""Profit calculation business logic.

Three-tier profit hierarchy:
  HourlyProfit → DailyProfit → MonthlyProfit

Profit formula:
  Retail fee = Σ(hourly consumption × (base_price × coefficient + price_difference))
  Wholesale fee = Σ(hourly consumption × wholesale_price)
  Market allocation fee = total consumption × market_allocation_price
  Total profit = Retail fee - Wholesale fee - Market allocation fee
"""

import calendar
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.profit import CustomerDailyProfit, CustomerHourlyProfit, CustomerMonthlyProfit
from app.models.customer_account import CustomerAccount
from app.models.agent import Agent
from app.models.commission import CommissionConfig
from app.models.consumption import CustomerDailyConsumption
from app.models.price import BasePrice, WholesalePrice, MarketAllocationPrice


# ========== Hourly Profit ==========


def list_hourly_profit_details(
    db: Session,
    customer_id: int,
    profit_date: Optional[date] = None,
    profit_month: Optional[str] = None,
) -> list:
    q = db.query(CustomerHourlyProfit).filter(
        CustomerHourlyProfit.customer_id == customer_id,
        CustomerHourlyProfit.deleted_at.is_(None),
    )
    if profit_date:
        q = q.filter(CustomerHourlyProfit.profit_date == profit_date)
    if profit_month:
        q = q.filter(CustomerHourlyProfit.profit_month == profit_month)
    return q.order_by(CustomerHourlyProfit.profit_date, CustomerHourlyProfit.hour).all()


def get_daily_profit_monthly_summary(db: Session, customer_id: int, profit_month: str) -> dict:
    """Get monthly summary from daily profit records."""
    rows = (
        db.query(CustomerDailyProfit)
        .filter(
            CustomerDailyProfit.customer_id == customer_id,
            CustomerDailyProfit.profit_month == profit_month,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .all()
    )
    total_consumption = sum((r.total_consumption or Decimal("0")) for r in rows)
    total_retail = sum((r.retail_fee or Decimal("0")) for r in rows)
    total_wholesale = sum((r.wholesale_fee or Decimal("0")) for r in rows)
    total_market = sum((r.market_allocation_fee or Decimal("0")) for r in rows)
    total_profit = sum((r.total_profit or Decimal("0")) for r in rows)
    days_with_data = len(rows)
    return {
        "customer_id": customer_id,
        "profit_month": profit_month,
        "days_with_data": days_with_data,
        "total_consumption": total_consumption,
        "total_retail_fee": total_retail,
        "total_wholesale_fee": total_wholesale,
        "total_market_allocation_fee": total_market,
        "total_profit": total_profit,
    }


def batch_calculate_daily_profit(db: Session, start_date: date, end_date: date) -> dict:
    """Batch calculate daily profits for all customers with consumption data."""
    from app.models.consumption import CustomerDailyConsumption

    consumptions = (
        db.query(CustomerDailyConsumption)
        .filter(
            CustomerDailyConsumption.data_date >= start_date,
            CustomerDailyConsumption.data_date <= end_date,
            CustomerDailyConsumption.deleted_at.is_(None),
        )
        .all()
    )

    processed = set()
    success_list = []
    failure_list = []

    for c in consumptions:
        key = (c.customer_account_id, str(c.data_date))
        if key in processed:
            continue
        processed.add(key)
        try:
            result = calculate_daily_profit(db, c.customer_account_id, c.data_date)
            if result.get("success"):
                success_list.append({
                    "customer_account_id": c.customer_account_id,
                    "customer_name": c.customer_name,
                    "date": str(c.data_date),
                    "total_profit": str(result.get("total_profit", 0)),
                })
            else:
                failure_list.append({
                    "customer_account_id": c.customer_account_id,
                    "customer_name": c.customer_name,
                    "date": str(c.data_date),
                    "error": result.get("message"),
                })
        except Exception as e:
            failure_list.append({
                "customer_account_id": c.customer_account_id,
                "customer_name": c.customer_name,
                "date": str(c.data_date),
                "error": str(e),
            })

    return {
        "total_count": len(processed),
        "success_count": len(success_list),
        "failure_count": len(failure_list),
        "success_list": success_list,
        "failure_list": failure_list,
    }


def get_daily_hourly_detail(db: Session, customer_id: int, profit_date: date) -> list:
    return (
        db.query(CustomerHourlyProfit)
        .filter(
            CustomerHourlyProfit.customer_id == customer_id,
            CustomerHourlyProfit.profit_date == profit_date,
            CustomerHourlyProfit.deleted_at.is_(None),
        )
        .order_by(CustomerHourlyProfit.hour)
        .all()
    )


def get_monthly_hourly_detail(db: Session, customer_id: int, profit_month: str) -> list:
    return (
        db.query(CustomerHourlyProfit)
        .filter(
            CustomerHourlyProfit.customer_id == customer_id,
            CustomerHourlyProfit.profit_month == profit_month,
            CustomerHourlyProfit.deleted_at.is_(None),
        )
        .order_by(CustomerHourlyProfit.profit_date, CustomerHourlyProfit.hour)
        .all()
    )


def get_daily_hourly_summary(db: Session, customer_id: int, profit_date: date) -> dict:
    """Get hourly profit summary by time period for a specific day."""
    rows = (
        db.query(CustomerHourlyProfit)
        .filter(
            CustomerHourlyProfit.customer_id == customer_id,
            CustomerHourlyProfit.profit_date == profit_date,
            CustomerHourlyProfit.deleted_at.is_(None),
        )
        .all()
    )
    period_map: dict = {}
    total_consumption = Decimal("0")
    total_profit = Decimal("0")

    for r in rows:
        key = str(r.time_period or 0)
        if key not in period_map:
            period_map[key] = {
                "time_period": r.time_period,
                "time_period_name": r.time_period_name,
                "total_consumption": Decimal("0"),
                "total_retail_fee": Decimal("0"),
                "total_profit": Decimal("0"),
                "hour_count": 0,
            }
        period_map[key]["total_consumption"] += r.consumption or Decimal("0")
        period_map[key]["total_retail_fee"] += r.retail_fee or Decimal("0")
        period_map[key]["total_profit"] += r.profit or Decimal("0")
        period_map[key]["hour_count"] += 1
        total_consumption += r.consumption or Decimal("0")
        total_profit += r.profit or Decimal("0")

    return {
        "customer_id": customer_id,
        "profit_date": profit_date,
        "total_consumption": total_consumption,
        "total_profit": total_profit,
        "periods": list(period_map.values()),
    }


def get_hourly_average(db: Session, customer_id: int, profit_month: str) -> list:
    """Get hourly average profit data for a month."""
    from collections import defaultdict

    rows = get_monthly_hourly_detail(db, customer_id, profit_month)

    # Group by hour
    hour_groups: dict = defaultdict(list)
    for r in rows:
        hour_groups[r.hour or 0].append(r)

    result = []
    for hour in sorted(hour_groups.keys()):
        hour_data = hour_groups[hour]
        first = hour_data[0]
        day_count = len(hour_data)

        avg_consumption = sum((r.consumption or Decimal("0")) for r in hour_data) / day_count
        avg_profit = sum((r.profit or Decimal("0")) for r in hour_data) / day_count
        total_profit = sum((r.profit or Decimal("0")) for r in hour_data)

        result.append({
            "hour": hour,
            "time_start": first.time_start,
            "time_end": first.time_end,
            "time_period_name": first.time_period_name,
            "day_count": day_count,
            "avg_consumption": avg_consumption.quantize(Decimal("0.001")),
            "avg_profit": avg_profit.quantize(Decimal("0.01")),
            "total_profit": total_profit.quantize(Decimal("0.01")),
        })

    return result


def get_time_period_summary(db: Session, customer_id: int, profit_month: str) -> dict:
    """Aggregate hourly profit by time period for a month."""
    rows = (
        db.query(CustomerHourlyProfit)
        .filter(
            CustomerHourlyProfit.customer_id == customer_id,
            CustomerHourlyProfit.profit_month == profit_month,
            CustomerHourlyProfit.deleted_at.is_(None),
        )
        .all()
    )
    summary: dict = {}
    for r in rows:
        key = str(r.time_period or 0)
        if key not in summary:
            summary[key] = {
                "time_period": r.time_period,
                "time_period_name": r.time_period_name,
                "total_consumption": Decimal("0"),
                "total_retail_fee": Decimal("0"),
                "total_profit": Decimal("0"),
            }
        summary[key]["total_consumption"] += r.consumption or Decimal("0")
        summary[key]["total_retail_fee"] += r.retail_fee or Decimal("0")
        summary[key]["total_profit"] += r.profit or Decimal("0")
    return summary


# ========== Daily Profit ==========


def list_daily_profits(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    customer_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    profit_date: Optional[str] = None,
    profit_month: Optional[str] = None,
    status: Optional[int] = None,
) -> dict:
    q = db.query(CustomerDailyProfit).filter(CustomerDailyProfit.deleted_at.is_(None))
    if customer_id:
        q = q.filter(CustomerDailyProfit.customer_id == customer_id)
    if agent_id:
        q = q.filter(CustomerDailyProfit.agent_id == agent_id)
    if profit_date:
        q = q.filter(CustomerDailyProfit.profit_date == profit_date)
    if profit_month:
        q = q.filter(CustomerDailyProfit.profit_month == profit_month)
    if status is not None:
        q = q.filter(CustomerDailyProfit.status == status)
    total = q.count()
    items = (
        q.order_by(CustomerDailyProfit.profit_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_daily_profit(db: Session, id: int) -> Optional[CustomerDailyProfit]:
    return (
        db.query(CustomerDailyProfit)
        .filter(CustomerDailyProfit.id == id, CustomerDailyProfit.deleted_at.is_(None))
        .first()
    )


def get_daily_profit_by_date(
    db: Session, customer_id: int, profit_date: date
) -> Optional[CustomerDailyProfit]:
    return (
        db.query(CustomerDailyProfit)
        .filter(
            CustomerDailyProfit.customer_id == customer_id,
            CustomerDailyProfit.profit_date == profit_date,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .first()
    )


# ---------- Daily Profit Calculation Engine ----------


def _get_base_price_for_date(db: Session, target_date: date) -> Decimal:
    """Get the base price for a given date (monthly average)."""
    year, month = target_date.year, target_date.month
    from sqlalchemy import func

    result = (
        db.query(func.avg(BasePrice.price))
        .filter(
            func.extract("year", BasePrice.price_date) == year,
            func.extract("month", BasePrice.price_date) == month,
            BasePrice.deleted_at.is_(None),
        )
        .scalar()
    )
    if result is not None:
        return Decimal(str(result))
    # Fallback: get any matching record
    row = (
        db.query(BasePrice)
        .filter(
            func.extract("year", BasePrice.price_date) == year,
            func.extract("month", BasePrice.price_date) == month,
            BasePrice.deleted_at.is_(None),
        )
        .first()
    )
    if row:
        return row.price
    raise ValueError(f"未找到基准价格数据: {target_date}")


def _get_wholesale_price_for_period(
    db: Session, target_date: date, time_period: int
) -> Decimal:
    """Get average wholesale price for a time period on a given date."""
    from sqlalchemy import func

    prices = (
        db.query(func.avg(WholesalePrice.wholesale_price))
        .filter(
            WholesalePrice.price_date == target_date,
            WholesalePrice.time_period == str(time_period),
            WholesalePrice.deleted_at.is_(None),
        )
        .scalar()
    )
    if prices is not None:
        return Decimal(str(prices))
    raise ValueError(f"未找到批发价格: {target_date}, 时段={time_period}")


def _get_market_allocation_price(db: Session, profit_month: str) -> Decimal:
    row = (
        db.query(MarketAllocationPrice)
        .filter(
            MarketAllocationPrice.year_month == profit_month,
            MarketAllocationPrice.deleted_at.is_(None),
        )
        .first()
    )
    if row and row.allocation_price:
        return row.allocation_price
    raise ValueError(f"未找到市场分摊价: {profit_month}")


def _get_commission_config(db: Session) -> tuple:
    """Get current commission rates. Returns (agent_rate, parent_rate)."""
    config = (
        db.query(CommissionConfig)
        .filter(
            CommissionConfig.deleted_at.is_(None),
        )
        .order_by(CommissionConfig.effective_month.desc())
        .first()
    )
    agent_rate = Decimal("0.50")
    parent_rate = Decimal("0.05")
    if config:
        if config.agent_commission_rate:
            agent_rate = config.agent_commission_rate / Decimal("100")
        if config.parent_commission_rate:
            parent_rate = config.parent_commission_rate / Decimal("100")
    return agent_rate, parent_rate


TIME_PERIOD_COEFFICIENTS = {
    "peak": Decimal("1.8"),
    "high": Decimal("1.5"),
    "normal": Decimal("1.0"),
    "valley": Decimal("0.5"),
}


def calculate_daily_profit(db: Session, customer_account_id: int, profit_date: date) -> dict:
    """Calculate daily profit from daily consumption data."""
    # Get daily consumption
    consumption = (
        db.query(CustomerDailyConsumption)
        .filter(
            CustomerDailyConsumption.customer_account_id == customer_account_id,
            CustomerDailyConsumption.data_date == profit_date,
            CustomerDailyConsumption.deleted_at.is_(None),
        )
        .first()
    )
    if not consumption:
        return {"success": False, "message": "未找到日用电量数据"}

    # Check existing profit record and delete
    existing = get_daily_profit_by_date(db, customer_account_id, profit_date)
    if existing:
        db.delete(existing)
        db.flush()

    # Get customer info
    customer = (
        db.query(CustomerAccount)
        .filter(
            CustomerAccount.id == customer_account_id,
            CustomerAccount.deleted_at.is_(None),
        )
        .first()
    )
    if not customer:
        return {"success": False, "message": "未找到客户信息"}

    # Check contract validity
    if customer.contract_end_date and customer.contract_end_date < profit_date:
        return {"success": False, "message": "客户不在合作有效期内"}

    # Get price difference from consumption record
    price_diff = consumption.price_difference
    if price_diff is None:
        return {"success": False, "message": "缺少价差信息"}
    price_diff_dec = Decimal(str(price_diff))

    profit_month = profit_date.strftime("%Y-%m")
    base_price = _get_base_price_for_date(db, profit_date)
    market_price = _get_market_allocation_price(db, profit_month)

    # Calculate retail fee by time period
    periods = [
        ("peak", consumption.peak_consumption),
        ("high", consumption.high_consumption),
        ("normal", consumption.normal_consumption),
        ("valley", consumption.valley_consumption),
    ]
    total_retail_fee = Decimal("0")
    total_wholesale_fee = Decimal("0")
    total_consumption = Decimal("0")

    for period_name, period_consumption in periods:
        if period_consumption is None or period_consumption <= 0:
            continue
        cons = Decimal(str(period_consumption))
        total_consumption += cons

        coeff = TIME_PERIOD_COEFFICIENTS.get(period_name, Decimal("1.0"))
        # Retail: unit_price = base_price × coefficient + price_difference
        unit_price = base_price * coeff + price_diff_dec
        retail_fee = cons * unit_price
        total_retail_fee += retail_fee

        # Wholesale
        period_map = {"peak": 1, "high": 2, "normal": 3, "valley": 4}
        wholesale_unit = _get_wholesale_price_for_period(
            db, profit_date, period_map[period_name]
        )
        wholesale_fee = cons * wholesale_unit
        total_wholesale_fee += wholesale_fee

    market_allocation_fee = total_consumption * market_price
    total_profit = total_retail_fee - total_wholesale_fee - market_allocation_fee

    # Round to 2 decimal places
    total_retail_fee = total_retail_fee.quantize(Decimal("0.01"))
    total_wholesale_fee = total_wholesale_fee.quantize(Decimal("0.01"))
    market_allocation_fee = market_allocation_fee.quantize(Decimal("0.01"))
    total_profit = total_profit.quantize(Decimal("0.01"))

    # Commission distribution
    agent_rate, parent_rate = _get_commission_config(db)
    agent_commission = (total_profit * agent_rate).quantize(Decimal("0.01"))
    parent_commission = (total_profit * parent_rate).quantize(Decimal("0.01"))
    company_commission = total_profit - agent_commission - parent_commission

    # Get agent info
    agent_name = None
    parent_agent_id = None
    parent_agent_name = None
    if customer.agent_id:
        agent = db.query(Agent).filter(Agent.id == customer.agent_id).first()
        if agent:
            agent_name = agent.name
            parent_agent_id = agent.parent_id
            if agent.parent_id:
                parent = db.query(Agent).filter(Agent.id == agent.parent_id).first()
                if parent:
                    parent_agent_name = parent.name

    # Create daily profit record
    daily_profit = CustomerDailyProfit(
        customer_id=customer_account_id,
        customer_name=customer.customer_name,
        profit_date=profit_date,
        profit_month=profit_month,
        agent_id=customer.agent_id,
        agent_name=agent_name,
        parent_agent_id=parent_agent_id,
        parent_agent_name=parent_agent_name,
        total_consumption=total_consumption,
        retail_fee=total_retail_fee,
        wholesale_fee=total_wholesale_fee,
        market_allocation_fee=market_allocation_fee,
        total_profit=total_profit,
        agent_commission_rate=agent_rate,
        agent_commission_amount=agent_commission,
        parent_commission_rate=parent_rate,
        parent_commission_amount=parent_commission,
        company_commission_amount=company_commission,
        price_difference=price_diff_dec,
        status=2,  # processed
    )
    db.add(daily_profit)
    db.commit()
    db.refresh(daily_profit)

    return {
        "success": True,
        "data": daily_profit,
        "total_profit": total_profit,
    }


# ========== Monthly Profit ==========


def list_monthly_profits(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    customer_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    profit_month: Optional[str] = None,
    status: Optional[int] = None,
) -> dict:
    q = db.query(CustomerMonthlyProfit).filter(CustomerMonthlyProfit.deleted_at.is_(None))
    if customer_id:
        q = q.filter(CustomerMonthlyProfit.customer_id == customer_id)
    if agent_id:
        q = q.filter(CustomerMonthlyProfit.agent_id == agent_id)
    if profit_month:
        q = q.filter(CustomerMonthlyProfit.profit_month == profit_month)
    if status is not None:
        q = q.filter(CustomerMonthlyProfit.status == status)
    total = q.count()
    items = (
        q.order_by(CustomerMonthlyProfit.profit_month.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_monthly_profit(db: Session, id: int) -> Optional[CustomerMonthlyProfit]:
    return (
        db.query(CustomerMonthlyProfit)
        .filter(CustomerMonthlyProfit.id == id, CustomerMonthlyProfit.deleted_at.is_(None))
        .first()
    )


def generate_monthly_profit(db: Session, customer_id: int, profit_month: str) -> dict:
    """Aggregate daily profits into a monthly profit record."""
    # Check if already exists
    existing = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.customer_id == customer_id,
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "该月利润已存在"}

    daily_rows = (
        db.query(CustomerDailyProfit)
        .filter(
            CustomerDailyProfit.customer_id == customer_id,
            CustomerDailyProfit.profit_month == profit_month,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .all()
    )
    if not daily_rows:
        return {"success": False, "message": "未找到该月的日利润数据"}

    total_consumption = sum((r.total_consumption or Decimal("0")) for r in daily_rows)
    total_retail = sum((r.retail_fee or Decimal("0")) for r in daily_rows)
    total_wholesale = sum((r.wholesale_fee or Decimal("0")) for r in daily_rows)
    total_market = sum((r.market_allocation_fee or Decimal("0")) for r in daily_rows)
    total_profit = sum((r.total_profit or Decimal("0")) for r in daily_rows)
    agent_commission = sum((r.agent_commission_amount or Decimal("0")) for r in daily_rows)
    parent_commission = sum((r.parent_commission_amount or Decimal("0")) for r in daily_rows)
    company_commission = sum((r.company_commission_amount or Decimal("0")) for r in daily_rows)

    first = daily_rows[0]
    year, month = profit_month.split("-")
    _, days_in_month = calendar.monthrange(int(year), int(month))

    monthly = CustomerMonthlyProfit(
        customer_id=customer_id,
        customer_name=first.customer_name,
        profit_month=profit_month,
        agent_id=first.agent_id,
        agent_name=first.agent_name,
        parent_agent_id=first.parent_agent_id,
        parent_agent_name=first.parent_agent_name,
        total_consumption=total_consumption,
        final_consumption=total_consumption,
        retail_fee=total_retail,
        wholesale_fee=total_wholesale,
        market_allocation_fee=total_market,
        total_profit=total_profit,
        adjusted_total_profit=total_profit,
        agent_commission_rate=first.agent_commission_rate,
        agent_commission_amount=agent_commission,
        parent_commission_rate=first.parent_commission_rate,
        parent_commission_amount=parent_commission,
        company_commission_amount=company_commission,
        status=1,
        data_days_count=len(daily_rows),
        expected_days_count=days_in_month,
        data_completeness_rate=Decimal(str(len(daily_rows))) / Decimal(str(days_in_month)),
    )
    db.add(monthly)
    db.commit()
    db.refresh(monthly)
    return {"success": True, "data": monthly}


def adjust_monthly_profit(
    db: Session,
    id: int,
    adjustment_consumption: Decimal,
    adjustment_remark: Optional[str] = None,
) -> dict:
    """Apply consumption adjustment and recalculate profit."""
    monthly = get_monthly_profit(db, id)
    if not monthly:
        return {"success": False, "message": "记录不存在"}
    if monthly.status and monthly.status >= 4:
        return {"success": False, "message": "已确认的利润不允许调平"}

    total_consumption = monthly.total_consumption or Decimal("0")
    total_profit = monthly.total_profit or Decimal("0")

    if total_consumption <= 0:
        return {"success": False, "message": "总用电量数据异常"}

    # Recalculate
    final_consumption = total_consumption + adjustment_consumption
    avg_unit_profit = total_profit / total_consumption
    adjustment_fee = (adjustment_consumption * avg_unit_profit).quantize(Decimal("0.01"))
    adjusted_profit = (total_profit + adjustment_fee).quantize(Decimal("0.01"))

    # Redistribute
    agent_rate, parent_rate = _get_commission_config(db)
    agent_commission = (adjusted_profit * agent_rate).quantize(Decimal("0.01"))
    parent_commission = (adjusted_profit * parent_rate).quantize(Decimal("0.01"))
    company_commission = adjusted_profit - agent_commission - parent_commission

    monthly.adjustment_consumption = adjustment_consumption
    monthly.final_consumption = final_consumption
    monthly.adjustment_fee = adjustment_fee
    monthly.adjusted_total_profit = adjusted_profit
    monthly.agent_commission_amount = agent_commission
    monthly.parent_commission_amount = parent_commission
    monthly.company_commission_amount = company_commission
    monthly.adjustment_status = 2
    monthly.status = 2
    monthly.adjustment_remark = adjustment_remark

    db.commit()
    db.refresh(monthly)
    return {"success": True, "data": monthly}


def confirm_monthly_profit(db: Session, ids: list[int], remark: Optional[str] = None) -> dict:
    """Confirm (lock) monthly profits."""
    updated = []
    for pid in ids:
        monthly = get_monthly_profit(db, pid)
        if monthly and monthly.status and monthly.status < 4:
            monthly.status = 4  # confirmed
            monthly.adjustment_remark = remark or monthly.adjustment_remark
            updated.append(pid)
    db.commit()
    return {"success": True, "updated_count": len(updated)}


def settle_monthly_profit(db: Session, id: int, remark: Optional[str] = None) -> dict:
    """Settle a monthly profit record."""
    monthly = get_monthly_profit(db, id)
    if not monthly:
        return {"success": False, "message": "记录不存在"}
    if monthly.status != 4:
        return {"success": False, "message": "请先确认利润再结算"}
    monthly.status = 5  # settled
    monthly.settlement_remark = remark
    db.commit()
    return {"success": True}


def get_monthly_profits_by_month(db: Session, profit_month: str) -> list:
    return (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .all()
    )


def batch_generate_monthly_profit(db: Session, profit_month: str) -> dict:
    """Batch generate monthly profits for all customers with daily data."""
    from app.models.consumption import CustomerDailyConsumption

    # Find all customers with daily consumption in this month
    customers = (
        db.query(CustomerDailyConsumption.customer_account_id)
        .filter(
            CustomerDailyConsumption.data_date >= date(int(profit_month[:4]), int(profit_month[5:7]), 1),
            CustomerDailyConsumption.data_date <= date(int(profit_month[:4]), int(profit_month[5:7]),
                calendar.monthrange(int(profit_month[:4]), int(profit_month[5:7]))[1]),
            CustomerDailyConsumption.deleted_at.is_(None),
        )
        .distinct()
        .all()
    )

    success_list = []
    failure_list = []
    for (cust_id,) in customers:
        result = generate_monthly_profit(db, cust_id, profit_month)
        if result.get("success"):
            success_list.append({"customer_id": cust_id, "data": result.get("data")})
        else:
            failure_list.append({"customer_id": cust_id, "message": result.get("message")})

    return {
        "profit_month": profit_month,
        "total": len(customers),
        "success_count": len(success_list),
        "failure_count": len(failure_list),
        "success_list": success_list,
        "failure_list": failure_list,
    }


def recalculate_adjusted_profit(db: Session, id: int) -> dict:
    """Recalculate profit after adjustment."""
    monthly = get_monthly_profit(db, id)
    if not monthly:
        return {"success": False, "message": "记录不存在"}
    if monthly.adjustment_consumption is None or monthly.adjustment_status != 2:
        return {"success": False, "message": "未进行调平操作"}
    if monthly.status and monthly.status >= 4:
        return {"success": False, "message": "已确认的利润不允许重算"}

    total_consumption = monthly.total_consumption or Decimal("0")
    total_profit = monthly.total_profit or Decimal("0")

    if total_consumption <= 0:
        return {"success": False, "message": "总用电量数据异常"}

    adj_consumption = monthly.adjustment_consumption or Decimal("0")
    final_consumption = total_consumption + adj_consumption
    avg_unit_profit = total_profit / total_consumption
    adjustment_fee = (adj_consumption * avg_unit_profit).quantize(Decimal("0.01"))
    adjusted_profit = (total_profit + adjustment_fee).quantize(Decimal("0.01"))

    agent_rate, parent_rate = _get_commission_config(db)
    agent_commission = (adjusted_profit * agent_rate).quantize(Decimal("0.01"))
    parent_commission = (adjusted_profit * parent_rate).quantize(Decimal("0.01"))
    company_commission = adjusted_profit - agent_commission - parent_commission

    monthly.final_consumption = final_consumption
    monthly.adjustment_fee = adjustment_fee
    monthly.adjusted_total_profit = adjusted_profit
    monthly.agent_commission_amount = agent_commission
    monthly.parent_commission_amount = parent_commission
    monthly.company_commission_amount = company_commission
    db.commit()
    db.refresh(monthly)
    return {"success": True, "data": monthly}


def batch_recalculate_adjusted_profit(db: Session, ids: list[int]) -> dict:
    """Batch recalculate adjusted profits."""
    success_list = []
    failure_list = []
    for pid in ids:
        result = recalculate_adjusted_profit(db, pid)
        if result.get("success"):
            success_list.append(pid)
        else:
            failure_list.append({"id": pid, "message": result.get("message")})
    return {
        "total": len(ids),
        "success_count": len(success_list),
        "failure_count": len(failure_list),
        "success_list": success_list,
        "failure_list": failure_list,
    }


def get_agent_monthly_summary(db: Session, profit_month: str) -> list:
    """Get agent-level monthly profit summary."""
    rows = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .all()
    )
    agent_map: dict = {}
    for r in rows:
        aid = r.agent_id or 0
        if aid not in agent_map:
            agent_map[aid] = {
                "agent_id": aid,
                "agent_name": r.agent_name,
                "customer_count": 0,
                "total_consumption": Decimal("0"),
                "total_profit": Decimal("0"),
                "agent_commission": Decimal("0"),
                "company_commission": Decimal("0"),
            }
        agent_map[aid]["customer_count"] += 1
        agent_map[aid]["total_consumption"] += r.total_consumption or Decimal("0")
        agent_map[aid]["total_profit"] += r.total_profit or Decimal("0")
        agent_map[aid]["agent_commission"] += r.agent_commission_amount or Decimal("0")
        agent_map[aid]["company_commission"] += r.company_commission_amount or Decimal("0")
    return list(agent_map.values())


def check_monthly_data_completeness(db: Session, profit_month: str) -> dict:
    """Check data completeness for a profit month."""
    year, month = profit_month.split("-")
    _, days_in_month = calendar.monthrange(int(year), int(month))

    # Count daily profit records per customer
    from sqlalchemy import func

    daily_counts = (
        db.query(
            CustomerDailyProfit.customer_id,
            func.count(CustomerDailyProfit.id).label("day_count"),
        )
        .filter(
            CustomerDailyProfit.profit_month == profit_month,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .group_by(CustomerDailyProfit.customer_id)
        .all()
    )

    customer_details = [
        {
            "customer_id": row.customer_id,
            "days_with_data": row.day_count,
            "expected_days": days_in_month,
            "completeness": round(row.day_count / days_in_month, 4),
        }
        for row in daily_counts
    ]

    total_customers = len(customer_details)
    fully_complete = sum(1 for c in customer_details if c["days_with_data"] >= days_in_month)

    return {
        "profit_month": profit_month,
        "expected_days": days_in_month,
        "total_customers": total_customers,
        "fully_complete_customers": fully_complete,
        "completeness_rate": round(fully_complete / total_customers, 4) if total_customers > 0 else 0,
        "details": customer_details,
    }


def get_monthly_profit_ranking(db: Session, profit_month: str, limit: int = 10) -> list:
    """Get monthly profit ranking by agent."""
    rows = (
        db.query(
            CustomerMonthlyProfit.agent_id,
            CustomerMonthlyProfit.agent_name,
            func.sum(CustomerMonthlyProfit.total_profit).label("total_profit"),
            func.sum(CustomerMonthlyProfit.total_consumption).label("total_consumption"),
            func.count(CustomerMonthlyProfit.id).label("customer_count"),
        )
        .filter(
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
            CustomerMonthlyProfit.agent_id.isnot(None),
        )
        .group_by(CustomerMonthlyProfit.agent_id, CustomerMonthlyProfit.agent_name)
        .order_by(func.sum(CustomerMonthlyProfit.total_profit).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "rank": i + 1,
            "agent_id": r.agent_id,
            "agent_name": r.agent_name,
            "customer_count": r.customer_count,
            "total_profit": r.total_profit,
            "total_consumption": r.total_consumption,
        }
        for i, r in enumerate(rows)
    ]


def get_agent_monthly_performance(db: Session, profit_month: str, agent_id: int) -> dict:
    """Get performance for a specific agent."""
    from sqlalchemy import func

    rows = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.agent_id == agent_id,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .all()
    )

    total_profit = sum((r.total_profit or Decimal("0")) for r in rows)
    total_consumption = sum((r.total_consumption or Decimal("0")) for r in rows)
    agent_commission = sum((r.agent_commission_amount or Decimal("0")) for r in rows)
    company_commission = sum((r.company_commission_amount or Decimal("0")) for r in rows)

    return {
        "agent_id": agent_id,
        "agent_name": rows[0].agent_name if rows else None,
        "profit_month": profit_month,
        "customer_count": len(rows),
        "total_consumption": total_consumption,
        "total_profit": total_profit,
        "agent_commission": agent_commission,
        "company_commission": company_commission,
    }


def generate_agent_fees_from_monthly_profits(
    db: Session, profit_month: str, agent_ids: Optional[list[int]] = None
) -> dict:
    """Generate agent fee records from monthly profits."""
    from app.models.commission import AgentFee
    from app.models.agent import Agent

    q = db.query(CustomerMonthlyProfit).filter(
        CustomerMonthlyProfit.profit_month == profit_month,
        CustomerMonthlyProfit.deleted_at.is_(None),
    )
    if agent_ids:
        q = q.filter(CustomerMonthlyProfit.agent_id.in_(agent_ids))
    rows = q.all()

    # Group by agent
    agent_fees_map: dict = {}
    for r in rows:
        aid = r.agent_id or 0
        if aid not in agent_fees_map:
            agent_fees_map[aid] = {
                "agent_id": aid,
                "agent_name": r.agent_name,
                "fee_month": profit_month,
                "total_profit": Decimal("0"),
                "commission_amount": Decimal("0"),
            }
        agent_fees_map[aid]["total_profit"] += r.total_profit or Decimal("0")
        agent_fees_map[aid]["commission_amount"] += r.agent_commission_amount or Decimal("0")

    created = []
    for aid, data in agent_fees_map.items():
        if aid == 0:
            continue
        # Check if already exists
        existing = (
            db.query(AgentFee)
            .filter(
                AgentFee.agent_id == aid,
                AgentFee.fee_month == profit_month,
                AgentFee.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            continue
        agent = db.query(Agent).filter(Agent.id == aid).first()
        agent_fee = AgentFee(
            agent_id=aid,
            agent_name=data["agent_name"],
            fee_month=profit_month,
            total_customer_profit=data["total_profit"],
            commission_amount=data["commission_amount"],
            status=1,  # pending
            profit_month=profit_month,
        )
        db.add(agent_fee)
        created.append(aid)

    db.commit()
    return {
        "profit_month": profit_month,
        "agent_count": len(agent_fees_map),
        "created_count": len(created),
        "created_agent_ids": created,
    }


def export_monthly_profit_excel(
    db: Session, profit_month: str, agent_id: Optional[int] = None
) -> StreamingResponse:
    """Export monthly profits as Excel."""
    from app.services.excel_utils import export_to_response

    q = db.query(CustomerMonthlyProfit).filter(
        CustomerMonthlyProfit.profit_month == profit_month,
        CustomerMonthlyProfit.deleted_at.is_(None),
    )
    if agent_id:
        q = q.filter(CustomerMonthlyProfit.agent_id == agent_id)
    rows = q.order_by(CustomerMonthlyProfit.customer_name).all()

    status_map = {1: "待确认", 2: "已调平", 4: "已确认", 5: "已结算"}
    headers = [
        "客户ID", "客户名称", "月份", "代理商",
        "总用电量(kWh)", "零售电费", "批发电费", "市场分摊费",
        "总利润", "调整后利润", "代理佣金", "公司利润",
    ]
    data = []
    for r in rows:
        data.append([
            r.customer_id, r.customer_name or "", r.profit_month, r.agent_name or "",
            float(r.total_consumption or 0),
            float(r.retail_fee or 0),
            float(r.wholesale_fee or 0),
            float(r.market_allocation_fee or 0),
            float(r.total_profit or 0),
            float(r.adjusted_total_profit or 0),
            float(r.agent_commission_amount or 0),
            float(r.company_commission_amount or 0),
        ])

    filename = f"客户月度利润_{profit_month}.xlsx"
    return export_to_response(headers, data, filename, f"月度利润_{profit_month}")


def get_monthly_profit_summary(db: Session, profit_month: str, agent_id: Optional[int] = None) -> dict:
    """Get monthly profit summary statistics."""
    q = db.query(CustomerMonthlyProfit).filter(
        CustomerMonthlyProfit.profit_month == profit_month,
        CustomerMonthlyProfit.deleted_at.is_(None),
    )
    if agent_id:
        q = q.filter(CustomerMonthlyProfit.agent_id == agent_id)

    rows = q.all()
    total_profit = sum((r.total_profit or Decimal("0")) for r in rows)
    total_consumption = sum((r.total_consumption or Decimal("0")) for r in rows)
    total_retail = sum((r.retail_fee or Decimal("0")) for r in rows)
    company_profit = sum((r.company_commission_amount or Decimal("0")) for r in rows)
    agent_profit = sum((r.agent_commission_amount or Decimal("0")) for r in rows)

    return {
        "profit_month": profit_month,
        "customer_count": len(rows),
        "total_consumption": total_consumption,
        "total_retail_fee": total_retail,
        "total_profit": total_profit,
        "company_profit": company_profit,
        "agent_profit": agent_profit,
    }
