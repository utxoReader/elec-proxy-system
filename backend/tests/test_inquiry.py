"""Inquiry module endpoint tests."""

from decimal import Decimal


def test_app_imports():
    """Smoke test that the app still imports with the inquiry router."""
    from app.main import app

    assert app is not None


def test_create_inquiry(client):
    """Create inquiry endpoint returns generated inquiry number."""
    payload = {
        "customer_name": "Test Inquiry Customer",
        "contact_person": "Alice",
        "contact_phone": "13800138000",
        "voltage_level": "10kV",
        "customer_type": 1,
        "usage_month": "2024-06",
        "estimated_monthly_consumption": "10000.0000",
        "usage_address": "Test Address",
        "industry_type": "制造业",
        "data_submit_type": 1,
        "consumption_data_json": {"hours": {f"hour_{h:02d}": "100" for h in range(24)}},
        "remark": "Test remark",
    }
    resp = client.post("/api/elec/inquiry/create", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "id" in body["data"]
    assert body["data"]["inquiry_no"].startswith("XJ")

    record_id = body["data"]["id"]

    get_resp = client.get(f"/api/elec/inquiry/get/{record_id}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["success"] is True
    assert get_body["data"]["customer_name"] == "Test Inquiry Customer"
    assert get_body["data"]["consumption_data_json"]["hours"]["hour_00"] == "100"


def test_update_inquiry(client):
    """Update inquiry basic info."""
    payload = {
        "customer_name": "Update Customer",
        "usage_month": "2024-07",
        "data_submit_type": 2,
        "peak_consumption": "1000.0000",
        "high_consumption": "2000.0000",
        "normal_consumption": "3000.0000",
        "valley_consumption": "4000.0000",
    }
    create_resp = client.post("/api/elec/inquiry/create", json=payload)
    record_id = create_resp.json()["data"]["id"]

    update_payload = {
        "id": record_id,
        "contact_person": "Bob",
        "estimated_monthly_consumption": "15000.0000",
    }
    update_resp = client.put("/api/elec/inquiry/update", json=update_payload)
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["success"] is True

    get_resp = client.get(f"/api/elec/inquiry/get/{record_id}")
    assert get_resp.json()["data"]["contact_person"] == "Bob"
    assert get_resp.json()["data"]["estimated_monthly_consumption"] == "15000.0000"


def test_status_transitions(client):
    """Quote -> accept -> cooperate -> terminate status transitions."""
    payload = {
        "customer_name": "Transition Customer",
        "usage_month": "2024-08",
        "estimated_monthly_consumption": "5000.0000",
    }
    create_resp = client.post("/api/elec/inquiry/create", json=payload)
    record_id = create_resp.json()["data"]["id"]

    quote_payload = {
        "price_difference": "0.050000",
        "recommended_package_type": 1,
        "quote_valid_until": "2024-12-31T23:59:59+08:00",
        "estimated_monthly_fee": "30000.0000",
        "estimated_savings": "2000.0000",
        "savings_rate": "0.0625",
    }
    quote_resp = client.post(f"/api/elec/inquiry/{record_id}/quote", json=quote_payload)
    assert quote_resp.status_code == 200
    assert quote_resp.json()["data"]["status"] == 2

    accept_resp = client.post(f"/api/elec/inquiry/{record_id}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["data"]["status"] == 3

    cooperate_resp = client.post(
        f"/api/elec/inquiry/{record_id}/cooperate",
        json={"cooperation_start_date": "2024-09-01", "cooperation_end_date": "2025-08-31"},
    )
    assert cooperate_resp.status_code == 200
    assert cooperate_resp.json()["data"]["status"] == 6

    terminate_resp = client.post(
        f"/api/elec/inquiry/{record_id}/terminate",
        json={"terminate_date": "2025-08-31"},
    )
    assert terminate_resp.status_code == 200
    assert terminate_resp.json()["data"]["status"] == 4


def test_reject_inquiry(client):
    """Quote -> reject transition."""
    payload = {"customer_name": "Reject Customer", "usage_month": "2024-09"}
    create_resp = client.post("/api/elec/inquiry/create", json=payload)
    record_id = create_resp.json()["data"]["id"]

    quote_payload = {
        "price_difference": "0.050000",
        "recommended_package_type": 1,
        "quote_valid_until": "2024-12-31T23:59:59+08:00",
        "estimated_monthly_fee": "30000.0000",
        "estimated_savings": "2000.0000",
        "savings_rate": "0.0625",
    }
    client.post(f"/api/elec/inquiry/{record_id}/quote", json=quote_payload)

    reject_resp = client.post(
        f"/api/elec/inquiry/{record_id}/reject",
        json={"reject_reason": "价格不合适"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["status"] == 4


def test_statistics_endpoint(client):
    """Statistics endpoint returns status counts."""
    resp = client.get("/api/elec/inquiry/statistics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "total" in body["data"]
    assert "pending" in body["data"]
    assert "quoted" in body["data"]
    assert "accepted" in body["data"]
    assert "cooperated" in body["data"]


def test_calculate_price_endpoint(client):
    """Calculate price endpoint returns fee and savings."""
    payload = {
        "package_type": 1,
        "estimated_consumption": "10000.0000",
        "price_difference": "0.050000",
        "grid_price": "0.600000",
    }
    resp = client.post("/api/elec/inquiry/calculate-price", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "estimated_monthly_fee" in body["data"]
    assert "estimated_savings" in body["data"]
    assert "savings_rate" in body["data"]
    assert Decimal(body["data"]["estimated_monthly_fee"]) == Decimal("6500.0000")


def test_export_inquiries(client):
    """Export endpoint returns Excel bytes."""
    resp = client.get("/api/elec/inquiry/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(resp.content) > 0
