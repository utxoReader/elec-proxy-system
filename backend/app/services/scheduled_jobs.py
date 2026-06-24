"""Idempotent scheduled job functions for the Tongye electricity proxy system.

Each function accepts a SQLAlchemy Session and an optional target date/month,
processes records one by one, catches per-record exceptions, logs them and
continues.  Successful updates are committed per record so that a single
failure does not roll back previous work.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.customer_account import CustomerAccount, CustomerAccountPriceHistory
from app.models.profit import CustomerDailyProfit, CustomerMonthlyProfit
from app.services.commission import generate_agent_fee_from_monthly_profit
from app.services.profit import calculate_daily_profit, generate_monthly_profit

logger = logging.getLogger(__name__)


def _previous_month(target: date | None = None) -> str:
    """Return the previous calendar month in 'YYYY-MM' format."""
    ref = target or date.today()
    first_day = ref.replace(day=1)
    last_day_of_prev = first_day - timedelta(days=1)
    return last_day_of_prev.strftime("%Y-%m")


def _yesterday() -> date:
    """Return yesterday's date."""
    return date.today() - timedelta(days=1)


def run_daily_profit_calculation(
    db: Session,
    target_date: date | None = None,
) -> dict[str, Any]:
    """Calculate daily profit for all active contracted customers.

    Args:
        db: SQLAlchemy session.
        target_date: Date to calculate profit for. Defaults to yesterday.

    Returns:
        Summary dict with processed_count, success_count, failed_count,
        skipped_count and errors.
    """
    target_date = target_date or _yesterday()
    customers = (
        db.query(CustomerAccount)
        .filter(
            CustomerAccount.customer_status == 3,
            CustomerAccount.deleted_at.is_(None),
        )
        .all()
    )

    success_count = 0
    failed_count = 0
    skipped_count = 0
    errors: list[dict[str, Any]] = []

    for customer in customers:
        try:
            result = calculate_daily_profit(db, customer.id, target_date)
            if result.get("success"):
                success_count += 1
            else:
                message = result.get("message", "")
                if message == "客户不在合作有效期内":
                    skipped_count += 1
                elif message == "未找到日用电量数据":
                    # No consumption data for the day is a normal skip condition.
                    skipped_count += 1
                else:
                    failed_count += 1
                    errors.append(
                        {
                            "customer_id": customer.id,
                            "customer_name": customer.customer_name,
                            "error": message or "calculate_daily_profit failed",
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Daily profit calculation failed for customer %s", customer.id)
            failed_count += 1
            errors.append(
                {
                    "customer_id": customer.id,
                    "customer_name": customer.customer_name,
                    "error": str(exc),
                }
            )
            db.rollback()

    return {
        "target_date": target_date.isoformat(),
        "processed_count": len(customers),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "errors": errors,
    }


def run_monthly_profit_aggregation(
    db: Session,
    target_month: str | None = None,
) -> dict[str, Any]:
    """Aggregate daily profits into monthly profits for a given month.

    Args:
        db: SQLAlchemy session.
        target_month: Month in 'YYYY-MM'. Defaults to previous month.

    Returns:
        Summary dict with processed_count, success_count, failed_count,
        skipped_count and errors.
    """
    target_month = target_month or _previous_month()
    customer_ids = (
        db.query(CustomerDailyProfit.customer_id)
        .filter(
            CustomerDailyProfit.profit_month == target_month,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .distinct()
        .all()
    )

    success_count = 0
    failed_count = 0
    skipped_count = 0
    errors: list[dict[str, Any]] = []

    for (customer_id,) in customer_ids:
        try:
            result = generate_monthly_profit(db, customer_id, target_month)
            if result.get("success"):
                success_count += 1
            else:
                message = result.get("message", "")
                if message == "该月利润已存在":
                    skipped_count += 1
                else:
                    failed_count += 1
                    errors.append(
                        {
                            "customer_id": customer_id,
                            "error": message or "generate_monthly_profit failed",
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Monthly profit aggregation failed for customer %s", customer_id)
            failed_count += 1
            errors.append({"customer_id": customer_id, "error": str(exc)})
            db.rollback()

    return {
        "target_month": target_month,
        "processed_count": len(customer_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "errors": errors,
    }


def run_monthly_commission_settlement(
    db: Session,
    target_month: str | None = None,
) -> dict[str, Any]:
    """Generate agent fees from monthly profit records for a given month.

    Args:
        db: SQLAlchemy session.
        target_month: Month in 'YYYY-MM'. Defaults to previous month.

    Returns:
        Summary dict with processed_count, success_count, failed_count,
        skipped_count and errors.
    """
    target_month = target_month or _previous_month()
    monthly_profits = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.profit_month == target_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .all()
    )

    success_count = 0
    failed_count = 0
    skipped_count = 0
    errors: list[dict[str, Any]] = []

    for monthly in monthly_profits:
        try:
            result = generate_agent_fee_from_monthly_profit(db, monthly.id)
            if result.get("success"):
                success_count += 1
            else:
                message = result.get("message", "")
                if message == "该代理商费用已生成":
                    skipped_count += 1
                else:
                    failed_count += 1
                    errors.append(
                        {
                            "monthly_profit_id": monthly.id,
                            "customer_id": monthly.customer_id,
                            "error": message or "generate_agent_fee failed",
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Commission settlement failed for monthly profit %s", monthly.id
            )
            failed_count += 1
            errors.append(
                {
                    "monthly_profit_id": monthly.id,
                    "customer_id": monthly.customer_id,
                    "error": str(exc),
                }
            )
            db.rollback()

    return {
        "target_month": target_month,
        "processed_count": len(monthly_profits),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "errors": errors,
    }


def run_price_effective_job(
    db: Session,
    target_date: date | None = None,
) -> dict[str, Any]:
    """Apply pending price history records that become effective today.

    Args:
        db: SQLAlchemy session.
        target_date: Date to apply price changes for. Defaults to today.

    Returns:
        Summary dict with applied_count, skipped_count and errors.
    """
    target_date = target_date or date.today()
    histories = (
        db.query(CustomerAccountPriceHistory)
        .filter(
            CustomerAccountPriceHistory.effective_date == target_date,
            CustomerAccountPriceHistory.status == 1,
            CustomerAccountPriceHistory.deleted_at.is_(None),
        )
        .all()
    )

    applied_count = 0
    skipped_count = 0
    errors: list[dict[str, Any]] = []

    for history in histories:
        try:
            customer = (
                db.query(CustomerAccount)
                .filter(
                    CustomerAccount.id == history.customer_account_id,
                    CustomerAccount.deleted_at.is_(None),
                )
                .first()
            )
            if not customer:
                skipped_count += 1
                errors.append(
                    {
                        "history_id": history.id,
                        "customer_account_id": history.customer_account_id,
                        "error": "Customer account not found",
                    }
                )
                continue

            customer.price_difference = history.new_price_difference
            customer.contract_start_date = (
                history.new_contract_start_date or customer.contract_start_date
            )
            customer.contract_end_date = (
                history.new_contract_end_date or customer.contract_end_date
            )
            history.status = 2  # 已生效
            db.commit()
            applied_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Price effective job failed for history %s", history.id
            )
            errors.append(
                {
                    "history_id": history.id,
                    "customer_account_id": history.customer_account_id,
                    "error": str(exc),
                }
            )
            db.rollback()

    return {
        "target_date": target_date.isoformat(),
        "applied_count": applied_count,
        "skipped_count": skipped_count,
        "errors": errors,
    }


def run_contract_expiry_reminder(
    db: Session,
    days_before: int = 7,
) -> dict[str, Any]:
    """Find customers whose contracts expire within the next N days.

    Args:
        db: SQLAlchemy session.
        days_before: Number of days before expiry to look ahead. Defaults to 7.

    Returns:
        Summary dict with reminder_count and reminders list.
    """
    today = date.today()
    end_date = today + timedelta(days=days_before)

    customers = (
        db.query(CustomerAccount)
        .filter(
            CustomerAccount.contract_end_date >= today,
            CustomerAccount.contract_end_date <= end_date,
            CustomerAccount.customer_status != 4,
            CustomerAccount.deleted_at.is_(None),
        )
        .order_by(CustomerAccount.contract_end_date)
        .all()
    )

    reminders = [
        {
            "customer_id": customer.id,
            "customer_name": customer.customer_name,
            "contract_end_date": (
                customer.contract_end_date.isoformat()
                if customer.contract_end_date
                else None
            ),
        }
        for customer in customers
    ]

    return {
        "days_before": days_before,
        "reminder_count": len(reminders),
        "reminders": reminders,
    }
