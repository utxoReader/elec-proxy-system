"""End-to-end integration test for the Tongye electricity proxy system.

This test exercises the full business flow on the in-memory SQLite test
fixture defined in ``tests/conftest.py``.  It uses service functions directly
rather than HTTP endpoints so that authentication/authorization do not affect
the integration validation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.agent import AgentFee
from app.models.customer_account import CustomerAccount, CustomerAccountPriceHistory
from app.models.inquiry import Inquiry
from app.models.profit import CustomerDailyProfit, CustomerMonthlyProfit
from app.schemas.agent import AgentCreate
from app.schemas.commission import CommissionConfigCreate
from app.schemas.consumption import (
    CustomerDailyConsumptionCreate,
    CustomerHourlyConsumptionCreate,
    Point96DataCreate,
)
from app.schemas.customer import CustomerAccountCreate, CustomerStatusChange
from app.schemas.inquiry import InquiryCreate, QuotePayload
from app.schemas.price import (
    BasePriceCreate,
    GridPriceCreate,
    MarketAllocationCreate,
    WholesalePriceCreate,
)
from app.schemas.usage_curve_template import UsageCurveTemplateCreate
from app.services import agent as agent_service
from app.services import commission as commission_service
from app.services import consumption as consumption_service
from app.services import customer as customer_service
from app.services import inquiry as inquiry_service
from app.services import price as price_service
from app.services import profit as profit_service
from app.services import scheduled_jobs as jobs_service
from app.services.usage_curve_template import UsageCurveTemplateService


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _make_24h_hours(total: Decimal | None = None) -> dict[str, Decimal]:
    """Return a simple 24-hour curve (1 kWh per hour by default)."""
    value = Decimal("1.0000") if total is None else (total / Decimal("24")).quantize(Decimal("0.0001"))
    return {f"hour_{h:02d}": value for h in range(24)}


def _assert_success(result: dict, message: str = "service call") -> None:
    """Assert that a service function returned success."""
    assert result.get("success") is True, f"{message} failed: {result.get('message')}"


# -----------------------------------------------------------------------------
# Integration test
# -----------------------------------------------------------------------------


def test_end_to_end_business_flow(db: Session) -> None:
    """Run the complete business flow end-to-end and verify each step."""

    today = date.today()
    tomorrow = today + timedelta(days=1)
    profit_date = today - timedelta(days=2)
    profit_month = profit_date.strftime("%Y-%m")

    # -------------------------------------------------------------------------
    # 1. Setup base data
    # -------------------------------------------------------------------------

    # Agent
    agent = agent_service.create_agent(
        db,
        AgentCreate(name="Integration Agent", type=1, status=0, tax_type=2),
    )
    assert agent.id is not None
    assert agent.name == "Integration Agent"

    # Commission config for current month
    commission_config = commission_service.create_commission_config(
        db,
        CommissionConfigCreate(
            effective_month=today.strftime("%Y-%m"),
            agent_commission_rate=Decimal("50.0000"),
            parent_commission_rate=Decimal("5.0000"),
            company_commission_rate=Decimal("45.0000"),
            remark="Integration test config",
        ),
    )
    assert commission_config.id is not None
    assert commission_config.effective_month == today.strftime("%Y-%m")

    # Base price for the profit month
    base_price = price_service.create_base_price(
        db,
        BasePriceCreate(
            price_type=1,
            price_date=profit_date,
            hour_index=0,
            price=Decimal("0.500000"),
            status=0,
        ),
    )
    assert base_price.id is not None
    assert base_price.price == Decimal("0.500000")

    # Grid price for the profit month
    grid_price = price_service.create_grid_price(
        db,
        GridPriceCreate(
            year_month=profit_month,
            time_period=1,
            base_price=Decimal("0.500000"),
            price=Decimal("0.600000"),
            price_coefficient=Decimal("1.8000"),
            status=0,
        ),
    )
    assert grid_price.id is not None

    # Wholesale prices for each time period on the profit date
    wholesale_period_prices = {
        1: Decimal("0.300000"),  # peak
        2: Decimal("0.350000"),  # high
        3: Decimal("0.400000"),  # normal
        4: Decimal("0.250000"),  # valley
    }
    for period, unit_price in wholesale_period_prices.items():
        wp = price_service.create_wholesale_price(
            db,
            WholesalePriceCreate(
                price_date=profit_date,
                price_month=profit_month,
                hour_index=0,
                time_period=str(period),
                wholesale_price=unit_price,
                status=0,
            ),
        )
        assert wp.id is not None

    # Market allocation price for the profit month
    market_alloc = price_service.create_market_allocation(
        db,
        MarketAllocationCreate(
            year_month=profit_month,
            allocation_price=Decimal("0.020000"),
            price_date=profit_date,
            status=0,
        ),
    )
    assert market_alloc.id is not None
    assert market_alloc.allocation_price == Decimal("0.020000")

    # Usage curve template (even distribution across 24 hours)
    ratio = (Decimal("1") / Decimal("24")).quantize(Decimal("0.0001"))
    template_data = {"template_name": "Integration Template", "description": "E2E test"}
    for h in range(24):
        template_data[f"hour_{h:02d}_ratio"] = ratio
    template = UsageCurveTemplateService.create(
        db, UsageCurveTemplateCreate(**template_data)
    )
    assert template.id is not None

    # -------------------------------------------------------------------------
    # 2. Customer lifecycle
    # -------------------------------------------------------------------------

    customer = customer_service.create_customer(
        db,
        CustomerAccountCreate(
            customer_name="Integration Customer",
            customer_status=2,  # pending contract
            agent_id=agent.id,
            agent_name=agent.name,
            package_type=1,
            price_difference=Decimal("0.050000"),
            contract_start_date=profit_date - timedelta(days=30),
            contract_end_date=profit_date + timedelta(days=365),
            voltage_level="10kV",
        ),
    )
    assert customer.id is not None
    assert customer.customer_status == 2

    # Move to contracted status
    updated_customer = customer_service.update_customer_status(
        db,
        CustomerStatusChange(id=customer.id, customer_status=3),
    )
    assert updated_customer is not None
    assert updated_customer.customer_status == 3

    # Create a pending price history record effective tomorrow
    history = CustomerAccountPriceHistory(
        customer_account_id=customer.id,
        customer_name=customer.customer_name,
        old_price_difference=customer.price_difference,
        new_price_difference=Decimal("0.080000"),
        old_contract_start_date=customer.contract_start_date,
        old_contract_end_date=customer.contract_end_date,
        new_contract_start_date=customer.contract_start_date,
        new_contract_end_date=customer.contract_end_date,
        effective_date=tomorrow,
        change_reason="Integration test price change",
        change_type=1,
        status=1,  # pending
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    assert history.id is not None
    assert history.status == 1

    # Run the price effective job for tomorrow
    result = jobs_service.run_price_effective_job(db, target_date=tomorrow)
    assert result["applied_count"] == 1

    db.expire_all()
    customer = db.get(CustomerAccount, customer.id)
    assert customer is not None
    assert customer.price_difference == Decimal("0.080000")

    # -------------------------------------------------------------------------
    # 3. Consumption data
    # -------------------------------------------------------------------------

    # Daily consumption with 24h data and peak/high/normal/valley totals
    hours = _make_24h_hours()
    daily_cons = consumption_service.CustomerDailyConsumptionService.create(
        db,
        CustomerDailyConsumptionCreate(
            customer_account_id=customer.id,
            customer_name=customer.customer_name,
            data_date=profit_date,
            data_month=profit_month,
            hours=hours,
            total_consumption=sum(hours.values()),
            peak_consumption=Decimal("100.0000"),
            high_consumption=Decimal("200.0000"),
            normal_consumption=Decimal("300.0000"),
            valley_consumption=Decimal("400.0000"),
            package_type=customer.package_type,
            price_difference=customer.price_difference,
            data_type=1,
            data_source=1,
        ),
    )
    assert daily_cons.id is not None
    assert daily_cons.total_consumption == sum(hours.values())

    # Point96 data and conversion to 24h
    point96 = consumption_service.Point96DataService.create(
        db,
        Point96DataCreate(
            customer_account_id=customer.id,
            data_date=profit_date,
            points={
                "00:15": Decimal("1"),
                "00:30": Decimal("2"),
                "00:45": Decimal("3"),
                "01:00": Decimal("4"),
                "01:15": Decimal("5"),
                "01:30": Decimal("6"),
                "01:45": Decimal("7"),
                "02:00": Decimal("8"),
            },
        ),
    )
    assert point96.id is not None
    converted = consumption_service.Point96DataService.convert_to_daily(db, point96.id)
    assert converted["hours"]["hour_00"] == Decimal("10.0000")
    assert converted["hours"]["hour_01"] == Decimal("26.0000")

    # Hourly consumption records
    for h in range(24):
        hc = consumption_service.CustomerHourlyConsumptionService.create(
            db,
            CustomerHourlyConsumptionCreate(
                customer_account_id=customer.id,
                customer_name=customer.customer_name,
                data_date=profit_date,
                data_month=profit_month,
                hour_index=h,
                consumption=Decimal("10.0000"),
                time_period=(h % 4) + 1,
                package_type=customer.package_type,
            ),
        )
        assert hc.id is not None

    # -------------------------------------------------------------------------
    # 4. Profit calculation
    # -------------------------------------------------------------------------

    daily_profit_result = profit_service.calculate_daily_profit(
        db, customer.id, profit_date
    )
    _assert_success(daily_profit_result, "calculate_daily_profit")
    assert daily_profit_result["data"].id is not None

    daily_profit = (
        db.query(CustomerDailyProfit)
        .filter(
            CustomerDailyProfit.customer_id == customer.id,
            CustomerDailyProfit.profit_date == profit_date,
            CustomerDailyProfit.deleted_at.is_(None),
        )
        .first()
    )
    assert daily_profit is not None
    assert daily_profit.total_consumption == Decimal("1000.0000")
    assert daily_profit.retail_fee is not None
    assert daily_profit.total_profit is not None

    monthly_profit_result = profit_service.generate_monthly_profit(
        db, customer.id, profit_month
    )
    _assert_success(monthly_profit_result, "generate_monthly_profit")
    monthly_profit = monthly_profit_result["data"]
    assert monthly_profit.id is not None
    assert monthly_profit.profit_month == profit_month

    monthly = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.customer_id == customer.id,
            CustomerMonthlyProfit.profit_month == profit_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .first()
    )
    assert monthly is not None
    assert monthly.total_profit == daily_profit.total_profit

    # -------------------------------------------------------------------------
    # 5. Commission settlement
    # -------------------------------------------------------------------------

    fee_result = commission_service.generate_agent_fee_from_monthly_profit(
        db, monthly_profit.id
    )
    _assert_success(fee_result, "generate_agent_fee_from_monthly_profit")
    fee = fee_result["data"]
    assert fee.id is not None
    assert fee.agent_id == agent.id
    assert fee.settlement_status == 1
    assert fee.approval_status == 1

    approve_result = commission_service.approve_agent_fee(db, fee.id, approve_status=2)
    _assert_success(approve_result, "approve_agent_fee")
    db.expire_all()
    fee = db.get(AgentFee, fee.id)
    assert fee is not None
    assert fee.approval_status == 2

    settle_result = commission_service.settle_agent_fee(db, fee.id)
    _assert_success(settle_result, "settle_agent_fee")
    db.expire_all()
    fee = db.get(AgentFee, fee.id)
    assert fee is not None
    assert fee.settlement_status == 2
    assert fee.settlement_date is not None

    # -------------------------------------------------------------------------
    # 6. Inquiry flow
    # -------------------------------------------------------------------------

    inquiry = inquiry_service.create_inquiry(
        db,
        InquiryCreate(
            customer_name=customer.customer_name,
            usage_month=profit_month,
            estimated_monthly_consumption=Decimal("10000.0000"),
            data_submit_type=1,
            consumption_data_json={"hours": {f"hour_{h:02d}": "100" for h in range(24)}},
            voltage_level="10kV",
        ),
    )
    assert inquiry.id is not None
    assert inquiry.inquiry_status == 1  # pending
    assert inquiry.inquiry_no.startswith("XJ")

    quote_payload = QuotePayload(
        price_difference=Decimal("0.050000"),
        recommended_package_type=1,
        quote_valid_until=datetime.now(timezone.utc) + timedelta(days=7),
        estimated_monthly_fee=Decimal("6500.0000"),
        estimated_savings=Decimal("500.0000"),
        savings_rate=Decimal("0.0714"),
    )
    quoted = inquiry_service.quote_inquiry(db, inquiry.id, quote_payload)
    assert quoted is not None
    assert quoted.inquiry_status == 2

    accepted = inquiry_service.accept_inquiry(db, inquiry.id)
    assert accepted is not None
    assert accepted.inquiry_status == 3

    cooperated = inquiry_service.cooperate_inquiry(
        db,
        inquiry.id,
        cooperation_start_date=profit_date,
        cooperation_end_date=profit_date + timedelta(days=365),
    )
    assert cooperated is not None
    assert cooperated.inquiry_status == 6

    db.expire_all()
    inquiry_record = db.get(Inquiry, inquiry.id)
    assert inquiry_record is not None
    assert inquiry_record.inquiry_status == 6

    # -------------------------------------------------------------------------
    # 7. Scheduled jobs
    # -------------------------------------------------------------------------

    # Create a near-expiry customer so the reminder finds at least one record.
    near_expiry_customer = customer_service.create_customer(
        db,
        CustomerAccountCreate(
            customer_name="Near Expiry Customer",
            customer_status=3,
            price_difference=Decimal("0.050000"),
            contract_start_date=today - timedelta(days=30),
            contract_end_date=today + timedelta(days=5),
        ),
    )
    assert near_expiry_customer.id is not None

    reminder_result = jobs_service.run_contract_expiry_reminder(db, days_before=7)
    assert reminder_result["reminder_count"] >= 1
    reminder_ids = {r["customer_id"] for r in reminder_result["reminders"]}
    assert near_expiry_customer.id in reminder_ids
