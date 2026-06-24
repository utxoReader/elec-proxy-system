"""Tests for scheduled background job endpoints and service functions."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.models.agent import Agent
from app.models.customer_account import CustomerAccount, CustomerAccountPriceHistory


def test_app_imports():
    """Smoke test that the app still imports with the scheduled jobs router."""
    from app.main import app

    assert app is not None


def _create_agent_and_token(db):
    """Create a test agent and return an Authorization header dict."""
    agent = Agent(name="Test Agent", status=0)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    token = create_access_token(subject=agent.id, expires_delta=timedelta(hours=1))
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client, db, name: str, status: int = 3, **kwargs):
    headers = _create_agent_and_token(db)
    payload = {
        "customer_name": name,
        "customer_status": status,
        "price_difference": "0.050000",
        "contract_start_date": "2024-01-01",
        "contract_end_date": "2025-12-31",
    }
    payload.update(kwargs)
    resp = client.post("/api/elec/customer-account/create", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_daily_profit_job_endpoint(client):
    """Daily profit job endpoint returns ApiResponse shape."""
    resp = client.post("/api/elec/jobs/daily-profit/run", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "processed_count" in body["data"]
    assert "success_count" in body["data"]
    assert "failed_count" in body["data"]
    assert "errors" in body["data"]


def test_monthly_profit_job_endpoint(client):
    """Monthly profit aggregation endpoint returns ApiResponse shape."""
    resp = client.post(
        "/api/elec/jobs/monthly-profit/run", json={"target_month": "2024-06"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["target_month"] == "2024-06"
    assert "processed_count" in body["data"]


def test_monthly_commission_job_endpoint(client):
    """Monthly commission settlement endpoint returns ApiResponse shape."""
    resp = client.post(
        "/api/elec/jobs/monthly-commission/run", json={"target_month": "2024-06"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["target_month"] == "2024-06"
    assert "processed_count" in body["data"]


def test_price_effective_job_applies_history(client, db):
    """Price effective job applies a pending price history record."""
    customer_id = _create_customer(
        client,
        db,
        name="Price Effective Customer",
        price_difference="0.050000",
    )

    # Create a pending price history record directly.
    history = CustomerAccountPriceHistory(
        customer_account_id=customer_id,
        customer_name="Price Effective Customer",
        old_price_difference=Decimal("0.050000"),
        new_price_difference=Decimal("0.100000"),
        old_contract_start_date=date(2024, 1, 1),
        old_contract_end_date=date(2025, 12, 31),
        new_contract_start_date=date(2024, 6, 1),
        new_contract_end_date=date(2026, 12, 31),
        effective_date=date.today(),
        change_reason="Test price change",
        change_type=3,
        status=1,
    )
    db.add(history)
    db.commit()

    resp = client.post(
        "/api/elec/jobs/price-effective/run",
        json={"target_date": date.today().isoformat()},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["applied_count"] == 1

    # Verify the change was persisted by refreshing the model directly.
    db.expire_all()
    customer = db.get(CustomerAccount, customer_id)
    assert customer is not None
    assert customer.price_difference == Decimal("0.100000")
    assert customer.contract_start_date == date(2024, 6, 1)
    assert customer.contract_end_date == date(2026, 12, 31)


def test_contract_expiry_reminder_finds_customer(client, db):
    """Contract expiry reminder finds a customer with a near-expiry contract."""
    expiry = date.today() + timedelta(days=5)
    customer_id = _create_customer(
        client,
        db,
        name="Expiry Reminder Customer",
        contract_end_date=expiry.isoformat(),
    )

    resp = client.post("/api/elec/jobs/contract-expiry/run", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["reminder_count"] >= 1
    reminders = body["data"]["reminders"]
    assert any(r["customer_id"] == customer_id for r in reminders)
    assert any(r["customer_name"] == "Expiry Reminder Customer" for r in reminders)
