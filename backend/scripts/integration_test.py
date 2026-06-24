"""PostgreSQL end-to-end integration test script.

Usage:
    export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db"
    cd backend
    python scripts/integration_test.py

The script reads the database URL from the environment (or ``.env`` via
Pydantic settings) and validates that the migrated PostgreSQL database can
support the core business flow:

    1. Key tables contain data.
    2. A representative daily/monthly profit calculation runs.
    3. Commission settlement (agent fee generation/approval/settlement) runs.
    4. The contract expiry reminder job runs.

Exit codes:
    0 - All verification and flow steps succeeded.
    1 - One or more checks failed or an unhandled exception occurred.
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import date
from decimal import Decimal
from typing import Any

# Allow importing the ``app`` package when running the script directly.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app.database import SessionLocal, engine
from app.models.agent import Agent, AgentFee
from app.models.consumption import CustomerDailyConsumption
from app.models.customer_account import CustomerAccount
from app.models.inquiry import Inquiry
from app.models.price import BasePrice, MarketAllocationPrice, WholesalePrice
from app.models.profit import CustomerDailyProfit, CustomerMonthlyProfit
from app.services import commission as commission_service
from app.services import profit as profit_service
from app.services import price as price_service
from app.services import scheduled_jobs as jobs_service
from app.schemas.price import (
    BasePriceCreate,
    MarketAllocationCreate,
    WholesalePriceCreate,
)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


REQUIRED_TABLES = {
    "elec_agent": "agent",
    "elec_customer_account": "customer_account",
    "elec_base_price": "base_price",
    "elec_wholesale_price": "wholesale_price",
    "elec_market_allocation_price": "market_allocation_price",
    "elec_customer_daily_consumption": "daily_consumption",
    "elec_customer_daily_profit": "daily_profit",
    "elec_customer_monthly_profit": "monthly_profit",
    "elec_inquiry": "inquiry",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def table_count(db: SessionLocal, model_cls: type) -> int:
    """Return the soft-delete-aware row count for a model."""
    return db.query(model_cls).filter(model_cls.deleted_at.is_(None)).count()


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(title)
    print("=" * 60)


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)
    print(f"[ERROR] {message}")


def _prices_exist_for_date(db, profit_date: date, profit_month: str) -> bool:
    """Return True if required prices for ``profit_date`` are present."""
    from sqlalchemy import extract

    base = (
        db.query(BasePrice)
        .filter(
            extract("year", BasePrice.price_date) == profit_date.year,
            extract("month", BasePrice.price_date) == profit_date.month,
            BasePrice.deleted_at.is_(None),
        )
        .first()
    )
    wholesale = (
        db.query(WholesalePrice)
        .filter(
            WholesalePrice.price_date == profit_date,
            WholesalePrice.deleted_at.is_(None),
        )
        .count()
    )
    market = (
        db.query(MarketAllocationPrice)
        .filter(
            MarketAllocationPrice.year_month == profit_month,
            MarketAllocationPrice.deleted_at.is_(None),
        )
        .first()
    )
    return base is not None and wholesale >= 4 and market is not None


def _ensure_prices_for_date(
    db, profit_date: date, profit_month: str
) -> None:
    """Create sample price rows for ``profit_date`` if they are missing."""
    from sqlalchemy import extract

    existing_base = (
        db.query(BasePrice)
        .filter(
            extract("year", BasePrice.price_date) == profit_date.year,
            extract("month", BasePrice.price_date) == profit_date.month,
            BasePrice.deleted_at.is_(None),
        )
        .first()
    )
    if existing_base is None:
        price_service.create_base_price(
            db,
            BasePriceCreate(
                price_type=1,
                price_date=profit_date,
                hour_index=0,
                price=Decimal("0.500000"),
                status=0,
            ),
        )
        print(f"    已创建 sample base_price for {profit_month}")

    existing_wholesale = {
        row.time_period
        for row in db.query(WholesalePrice).filter(
            WholesalePrice.price_date == profit_date,
            WholesalePrice.deleted_at.is_(None),
        )
    }
    sample_wholesale = {
        "1": Decimal("0.300000"),
        "2": Decimal("0.350000"),
        "3": Decimal("0.400000"),
        "4": Decimal("0.250000"),
    }
    for period, unit_price in sample_wholesale.items():
        if period not in existing_wholesale:
            price_service.create_wholesale_price(
                db,
                WholesalePriceCreate(
                    price_date=profit_date,
                    price_month=profit_month,
                    hour_index=0,
                    time_period=period,
                    wholesale_price=unit_price,
                    status=0,
                ),
            )
            print(f"    已创建 sample wholesale_price period={period} for {profit_date}")

    existing_market = (
        db.query(MarketAllocationPrice)
        .filter(
            MarketAllocationPrice.year_month == profit_month,
            MarketAllocationPrice.deleted_at.is_(None),
        )
        .first()
    )
    if existing_market is None:
        price_service.create_market_allocation(
            db,
            MarketAllocationCreate(
                year_month=profit_month,
                allocation_price=Decimal("0.020000"),
                price_date=profit_date,
                status=0,
            ),
        )
        print(f"    已创建 sample market_allocation_price for {profit_month}")


# -----------------------------------------------------------------------------
# Main integration runner
# -----------------------------------------------------------------------------


def main() -> int:
    """Run the PostgreSQL integration test."""
    errors: list[str] = []
    summary: dict[str, Any] = {}

    print("桐叶售电代理系统 — PostgreSQL 端到端集成测试")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Database engine: {engine.url.render_as_string(hide_password=True)}")

    db = SessionLocal()
    try:
        # ------------------------------------------------------------------
        # 1. Verify key tables have data
        # ------------------------------------------------------------------
        print_section("1. 关键表数据量检查")
        counts = {
            "agent": table_count(db, Agent),
            "customer_account": table_count(db, CustomerAccount),
            "base_price": table_count(db, BasePrice),
            "wholesale_price": table_count(db, WholesalePrice),
            "market_allocation_price": table_count(db, MarketAllocationPrice),
            "daily_consumption": table_count(db, CustomerDailyConsumption),
            "daily_profit": table_count(db, CustomerDailyProfit),
            "monthly_profit": table_count(db, CustomerMonthlyProfit),
            "inquiry": table_count(db, Inquiry),
        }
        summary["table_counts"] = counts
        for name, count in counts.items():
            print(f"  {name:30s}: {count:6d}")

        # Tables that must already contain migrated data.
        must_have_data = [
            "agent",
            "customer_account",
            "base_price",
            "wholesale_price",
            "market_allocation_price",
            "daily_consumption",
            "inquiry",
        ]
        for name in must_have_data:
            if counts[name] == 0:
                add_error(errors, f"关键表 '{name}' 中没有数据")

        # ------------------------------------------------------------------
        # 2. Run representative business flow on real migrated data
        # ------------------------------------------------------------------
        print_section("2. 代表性业务流程验证")

        if counts["daily_consumption"] == 0 or counts["customer_account"] == 0:
            print("  跳过利润/佣金流程：缺少客户或用电量数据")
        else:
            # Pick one consumption row whose customer is still contracted on
            # that date so profit calculation will not be skipped.
            consumption = (
                db.query(CustomerDailyConsumption)
                .join(
                    CustomerAccount,
                    CustomerAccount.id == CustomerDailyConsumption.customer_account_id,
                )
                .filter(
                    CustomerDailyConsumption.customer_account_id.isnot(None),
                    CustomerDailyConsumption.deleted_at.is_(None),
                    CustomerAccount.deleted_at.is_(None),
                    CustomerAccount.customer_status == 3,
                    CustomerAccount.contract_end_date >= CustomerDailyConsumption.data_date,
                )
                .order_by(CustomerDailyConsumption.data_date.desc())
                .first()
            )

            if consumption is None:
                # Fallback: any valid consumption row.
                consumption = (
                    db.query(CustomerDailyConsumption)
                    .filter(
                        CustomerDailyConsumption.customer_account_id.isnot(None),
                        CustomerDailyConsumption.deleted_at.is_(None),
                    )
                    .order_by(CustomerDailyConsumption.data_date.desc())
                    .first()
                )

            if consumption is None:
                add_error(errors, "未找到有效的日用电量记录")
            else:
                customer_id = consumption.customer_account_id
                profit_date = consumption.data_date
                profit_month = consumption.data_month or profit_date.strftime("%Y-%m")

                customer = db.get(CustomerAccount, customer_id)
                if customer is None:
                    add_error(errors, f"客户 {customer_id} 不存在")
                else:
                    print(
                        f"  选中客户: id={customer.id}, name={customer.customer_name}, "
                        f"date={profit_date}, month={profit_month}"
                    )

                    # Ensure the customer has an agent (required for fee generation).
                    if customer.agent_id is None and counts["agent"] > 0:
                        first_agent = db.query(Agent).filter(Agent.deleted_at.is_(None)).first()
                        if first_agent is not None:
                            customer.agent_id = first_agent.id
                            customer.agent_name = first_agent.name
                            db.commit()
                            print(f"  为客户绑定代理商: {first_agent.name}")

                    # Make sure the required prices exist for the selected date.
                    if not _prices_exist_for_date(db, profit_date, profit_month):
                        print("  缺少该日期/月份的价格数据，创建 sample 价格")
                        _ensure_prices_for_date(db, profit_date, profit_month)

                    # Daily profit
                    try:
                        daily_result = profit_service.calculate_daily_profit(
                            db, customer.id, profit_date
                        )
                        if daily_result.get("success"):
                            summary["daily_profit"] = {
                                "customer_id": customer.id,
                                "profit_date": profit_date.isoformat(),
                                "total_profit": str(daily_result["total_profit"]),
                            }
                            print(
                                f"  日利润计算成功: total_profit={daily_result['total_profit']}"
                            )
                        else:
                            add_error(
                                errors,
                                f"日利润计算失败: {daily_result.get('message')}",
                            )
                    except Exception as exc:  # noqa: BLE001
                        add_error(errors, f"日利润计算异常: {exc}")
                        traceback.print_exc()

                    # Monthly profit
                    try:
                        monthly_result = profit_service.generate_monthly_profit(
                            db, customer.id, profit_month
                        )
                        if monthly_result.get("success"):
                            monthly = monthly_result["data"]
                            summary["monthly_profit"] = {
                                "id": monthly.id,
                                "profit_month": profit_month,
                                "total_profit": str(monthly.total_profit),
                            }
                            print(
                                f"  月度利润汇总成功: id={monthly.id}, "
                                f"total_profit={monthly.total_profit}"
                            )
                        elif monthly_result.get("message") == "该月利润已存在":
                            # Already present from migrated data; just load it.
                            monthly = (
                                db.query(CustomerMonthlyProfit)
                                .filter(
                                    CustomerMonthlyProfit.customer_id == customer.id,
                                    CustomerMonthlyProfit.profit_month == profit_month,
                                    CustomerMonthlyProfit.deleted_at.is_(None),
                                )
                                .first()
                            )
                            if monthly is not None:
                                summary["monthly_profit"] = {
                                    "id": monthly.id,
                                    "profit_month": profit_month,
                                    "total_profit": str(monthly.total_profit),
                                }
                                print(
                                    f"  月度利润已存在: id={monthly.id}, "
                                    f"total_profit={monthly.total_profit}"
                                )
                            else:
                                add_error(errors, "月度利润记录未找到")
                        else:
                            add_error(
                                errors,
                                f"月度利润汇总失败: {monthly_result.get('message')}",
                            )
                    except Exception as exc:  # noqa: BLE001
                        add_error(errors, f"月度利润汇总异常: {exc}")
                        traceback.print_exc()

                    # Commission settlement
                    monthly_id = summary.get("monthly_profit", {}).get("id")
                    if monthly_id and customer.agent_id:
                        try:
                            fee_result = (
                                commission_service.generate_agent_fee_from_monthly_profit(
                                    db, monthly_id
                                )
                            )
                            if fee_result.get("success"):
                                fee = fee_result["data"]
                                summary["agent_fee"] = {
                                    "id": fee.id,
                                    "commission_amount": str(fee.commission_amount),
                                }
                                print(
                                    f"  代理费生成成功: id={fee.id}, "
                                    f"amount={fee.commission_amount}"
                                )

                                # Approve
                                approve_result = commission_service.approve_agent_fee(
                                    db, fee.id, approve_status=2
                                )
                                if approve_result.get("success"):
                                    print("  代理费审批成功")
                                else:
                                    add_error(
                                        errors,
                                        f"代理费审批失败: {approve_result.get('message')}",
                                    )

                                # Settle
                                settle_result = commission_service.settle_agent_fee(
                                    db, fee.id
                                )
                                if settle_result.get("success"):
                                    print("  代理费结算成功")
                                else:
                                    add_error(
                                        errors,
                                        f"代理费结算失败: {settle_result.get('message')}",
                                    )
                            elif fee_result.get("message") == "该代理商费用已生成":
                                existing_fee = (
                                    db.query(AgentFee)
                                    .filter(
                                        AgentFee.customer_account_id == customer.id,
                                        AgentFee.fee_month == profit_month,
                                        AgentFee.deleted_at.is_(None),
                                    )
                                    .first()
                                )
                                if existing_fee is not None:
                                    summary["agent_fee"] = {
                                        "id": existing_fee.id,
                                        "commission_amount": str(
                                            existing_fee.commission_amount
                                        ),
                                    }
                                    print(
                                        f"  代理费已存在: id={existing_fee.id}, "
                                        f"amount={existing_fee.commission_amount}"
                                    )
                                else:
                                    add_error(errors, "代理费记录未找到")
                            else:
                                add_error(
                                    errors,
                                    f"代理费生成失败: {fee_result.get('message')}",
                                )
                        except Exception as exc:  # noqa: BLE001
                            add_error(errors, f"代理费结算异常: {exc}")
                            traceback.print_exc()
                    else:
                        print("  跳过代理费结算：缺少月度利润或客户未绑定代理商")

        # ------------------------------------------------------------------
        # 3. Scheduled jobs
        # ------------------------------------------------------------------
        print_section("3. 定时任务验证")
        try:
            reminder_result = jobs_service.run_contract_expiry_reminder(
                db, days_before=7
            )
            summary["contract_expiry_reminder"] = {
                "reminder_count": reminder_result["reminder_count"],
                "sample": reminder_result["reminders"][:3],
            }
            print(
                f"  合同到期提醒任务成功: 找到 {reminder_result['reminder_count']} 条即将到期合同"
            )
            for r in reminder_result["reminders"][:3]:
                print(
                    f"    - {r['customer_name']} (id={r['customer_id']}, "
                    f"end={r['contract_end_date']})"
                )
        except Exception as exc:  # noqa: BLE001
            add_error(errors, f"合同到期提醒任务异常: {exc}")
            traceback.print_exc()

        # ------------------------------------------------------------------
        # 4. Summary report
        # ------------------------------------------------------------------
        print_section("4. 集成测试汇总报告")
        print("表数据量:")
        for name, count in summary.get("table_counts", {}).items():
            print(f"  {name:30s}: {count:6d}")

        print("\n关键流程结果:")
        if "daily_profit" in summary:
            dp = summary["daily_profit"]
            print(
                f"  日利润计算: customer_id={dp['customer_id']}, "
                f"date={dp['profit_date']}, total_profit={dp['total_profit']}"
            )
        if "monthly_profit" in summary:
            mp = summary["monthly_profit"]
            print(
                f"  月度利润汇总: id={mp['id']}, "
                f"month={mp['profit_month']}, total_profit={mp['total_profit']}"
            )
        if "agent_fee" in summary:
            fee = summary["agent_fee"]
            print(
                f"  代理费结算: id={fee['id']}, commission_amount={fee['commission_amount']}"
            )
        if "contract_expiry_reminder" in summary:
            cr = summary["contract_expiry_reminder"]
            print(
                f"  合同到期提醒: reminder_count={cr['reminder_count']}"
            )

        if errors:
            print("\n错误列表:")
            for err in errors:
                print(f"  - {err}")
            print("\n结果: 失败")
            return 1

        print("\n结果: 成功")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] 集成测试运行异常: {exc}")
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
