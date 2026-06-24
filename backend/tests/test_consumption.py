"""Consumption module endpoint and conversion tests."""

from decimal import Decimal

from app.models.consumption import Point96Data
from app.models.usage_curve import UsageCurveTemplate
from app.services.conversion import peak_valley_to_24h, point96_to_24h


def test_app_imports():
    """Smoke test that the app still imports with new routers."""
    from app.main import app

    assert app is not None


def test_daily_consumption_crud_api(client):
    """Daily consumption endpoints return ApiResponse shape."""
    payload = {
        "customer_account_id": 1,
        "customer_name": "Test Customer",
        "data_date": "2024-06-01",
        "data_month": "2024-06",
        "hours": {f"hour_{h:02d}": str(h) for h in range(24)},
        "total_consumption": "276.0000",
    }

    create_resp = client.post("/api/elec/daily-consumption/create", json=payload)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["success"] is True
    assert "id" in body["data"]

    record_id = body["data"]["id"]

    get_resp = client.get(f"/api/elec/daily-consumption/get/{record_id}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["success"] is True
    assert get_body["data"]["customer_name"] == "Test Customer"
    assert "hours" in get_body["data"]
    assert len(get_body["data"]["hours"]) == 24

    page_resp = client.get("/api/elec/daily-consumption/page?page=1&page_size=10")
    assert page_resp.status_code == 200
    page_body = page_resp.json()
    assert page_body["success"] is True
    assert "list" in page_body["data"]
    assert "total" in page_body["data"]
    assert "pageNo" in page_body["data"]
    assert "pageSize" in page_body["data"]

    update_payload = {
        "id": record_id,
        "customer_name": "Updated Customer",
        "hours": {"hour_00": "10.0000"},
    }
    update_resp = client.put("/api/elec/daily-consumption/update", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["success"] is True

    stats_resp = client.get("/api/elec/daily-consumption/statistics?customer_account_id=1&data_month=2024-06")
    assert stats_resp.status_code == 200
    stats_body = stats_resp.json()
    assert stats_body["success"] is True
    assert "total_days" in stats_body["data"]

    delete_resp = client.delete(f"/api/elec/daily-consumption/delete/{record_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    get_after = client.get(f"/api/elec/daily-consumption/get/{record_id}")
    assert get_after.json()["success"] is False


def test_hourly_consumption_api(client):
    """Hourly consumption endpoints return ApiResponse shape."""
    payload = {
        "customer_account_id": 2,
        "data_date": "2024-06-01",
        "data_month": "2024-06",
        "hour_index": 10,
        "consumption": "100.5000",
        "time_period": 2,
    }
    resp = client.post("/api/elec/hourly-consumption/create", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True

    page_resp = client.get("/api/elec/hourly-consumption/page")
    assert page_resp.status_code == 200
    assert page_resp.json()["success"] is True


def test_usage_curve_template_api(client):
    """Usage curve template endpoints return ApiResponse shape."""
    payload = {
        "template_name": "Test Template",
        "description": "Test",
        "hour_00_ratio": "0.02",
        "hour_12_ratio": "0.05",
        "hour_00_peak_ratio": "0.03",
    }
    resp = client.post("/api/elec/usage-curve-template/create", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    template_id = body["data"]["id"]

    get_resp = client.get(f"/api/elec/usage-curve-template/get/{template_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["success"] is True


def test_import_task_api(client):
    """Import task endpoints return ApiResponse shape even when empty."""
    page_resp = client.get("/api/elec/import-task/page")
    assert page_resp.status_code == 200
    body = page_resp.json()
    assert body["success"] is True
    assert "list" in body["data"]
    assert "total" in body["data"]


def test_point96_to_24h_conversion():
    """Conversion aggregates 15-min points into hourly totals."""
    obj = Point96Data()
    # First hour: 1+2+3+4 = 10
    obj.p0015 = Decimal("1")
    obj.p0030 = Decimal("2")
    obj.p0045 = Decimal("3")
    obj.p0100 = Decimal("4")
    # Second hour: 5+6+7+8 = 26
    obj.p0115 = Decimal("5")
    obj.p0130 = Decimal("6")
    obj.p0145 = Decimal("7")
    obj.p0200 = Decimal("8")

    result = point96_to_24h(obj)
    assert result["hour_00"] == Decimal("10.0000")
    assert result["hour_01"] == Decimal("26.0000")
    for h in range(2, 24):
        assert result[f"hour_{h:02d}"] == Decimal("0.0000")


def test_peak_valley_to_24h_conversion():
    """Peak-valley split uses template ratios."""
    template = UsageCurveTemplate()
    for h in range(24):
        setattr(template, f"hour_{h:02d}_ratio", Decimal("0"))
    template.hour_10_ratio = Decimal("1")

    result = peak_valley_to_24h(
        Decimal("100"),
        Decimal("200"),
        Decimal("300"),
        Decimal("400"),
        template,
        is_peak_month=False,
    )
    assert result["hour_10"] == Decimal("1000.0000")
    for h in range(24):
        if h != 10:
            assert result[f"hour_{h:02d}"] == Decimal("0.0000")


def test_point96_conversion_api(client):
    """Point96 convert endpoint aggregates 15-min points into 24h."""
    payload = {
        "customer_account_id": 3,
        "data_date": "2024-06-01",
        "points": {
            "00:15": "1",
            "00:30": "2",
            "00:45": "3",
            "01:00": "4",
        },
    }
    create_resp = client.post("/api/elec/point96/create", json=payload)
    assert create_resp.status_code == 201
    record_id = create_resp.json()["data"]["id"]

    convert_resp = client.post(f"/api/elec/point96/convert-to-daily/{record_id}")
    assert convert_resp.status_code == 200
    body = convert_resp.json()
    assert body["success"] is True
    assert body["data"]["hours"]["hour_00"] == "10.0000"


def test_peak_valley_conversion_api(client):
    """Peak-valley conversion endpoint returns 24h allocation."""
    template_payload = {
        "template_name": "Peak Template",
        "hour_10_ratio": "1.0",
    }
    create_resp = client.post("/api/elec/usage-curve-template/create", json=template_payload)
    assert create_resp.status_code == 201
    template_id = create_resp.json()["data"]["id"]

    payload = {
        "template_id": template_id,
        "peak": "100",
        "high": "200",
        "normal": "300",
        "valley": "400",
        "is_peak_month": False,
    }
    resp = client.post("/api/elec/conversion/peak-valley-to-24h", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["hours"]["hour_10"] == "1000.0000"
