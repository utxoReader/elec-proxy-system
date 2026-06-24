#!/usr/bin/env python3
"""Deep business flow verification against localhost backend."""

import json
import sys
from decimal import Decimal
import httpx

BASE = "http://localhost:8000"
TIMEOUT = 15.0


def login(client: httpx.Client) -> str:
    r = client.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}, timeout=TIMEOUT)
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()["data"]["access_token"]


def post(client: httpx.Client, token: str, path: str, body: dict) -> dict:
    r = client.post(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"}, json=body, timeout=TIMEOUT)
    return {"status": r.status_code, "json": r.json() if r.status_code in (200, 201) else r.text[:200]}


def get(client: httpx.Client, token: str, path: str) -> dict:
    r = client.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    return {"status": r.status_code, "json": r.json() if r.status_code == 200 else r.text[:200]}


def main():
    client = httpx.Client()
    token = login(client)
    results = []

    # Commission config
    results.append(("Create commission config", post(client, token, "/api/elec/commission-config/create", {
        "effective_month": "2024-06",
        "agent_commission_rate": "50.0000",
        "parent_commission_rate": "5.0000",
        "company_commission_rate": "45.0000",
    })))

    # Prices (schemas are per-hour / per-period)
    results.append(("Create base price", post(client, token, "/api/elec/base-price/create", {
        "price_type": 1,
        "price_date": "2024-06-01",
        "hour_index": 8,
        "price": "0.5000",
    })))

    results.append(("Create grid price", post(client, token, "/api/elec/grid-price/create", {
        "year_month": "2024-06",
        "time_period": 2,
        "price": "0.1500",
    })))

    results.append(("Create wholesale price", post(client, token, "/api/elec/wholesale-price/create", {
        "price_date": "2024-06-01",
        "price_month": "2024-06",
        "hour_index": 8,
        "time_period": "峰",
        "wholesale_price": "0.3500",
    })))

    # Customer
    results.append(("Create customer", post(client, token, "/api/elec/customer-account/create", {
        "customer_name": "Flow Customer",
        "customer_status": 3,
        "price_difference": "0.0500",
        "contract_start_date": "2024-01-01",
        "contract_end_date": "2025-12-31",
    })))

    customer_id = results[-1][1]["json"].get("data", {}).get("id")

    # Daily consumption
    results.append(("Create daily consumption", post(client, token, "/api/elec/daily-consumption/create", {
        "customer_account_id": customer_id,
        "data_date": "2024-06-01",
        "total_consumption": "240.0000",
        "hour_00": "10.0000", "hour_01": "10.0000", "hour_02": "10.0000", "hour_03": "10.0000",
        "hour_04": "10.0000", "hour_05": "10.0000", "hour_06": "10.0000", "hour_07": "10.0000",
        "hour_08": "10.0000", "hour_09": "10.0000", "hour_10": "10.0000", "hour_11": "10.0000",
        "hour_12": "10.0000", "hour_13": "10.0000", "hour_14": "10.0000", "hour_15": "10.0000",
        "hour_16": "10.0000", "hour_17": "10.0000", "hour_18": "10.0000", "hour_19": "10.0000",
        "hour_20": "10.0000", "hour_21": "10.0000", "hour_22": "10.0000", "hour_23": "10.0000",
    })))

    # Run daily profit job
    results.append(("Run daily profit job", post(client, token, "/api/elec/jobs/daily-profit/run", {
        "date": "2024-06-01",
    })))

    # Check daily profit
    results.append(("Query daily profit", get(client, token, f"/api/elec/customer-daily-profit/page?customer_account_id={customer_id}&page=1&page_size=20")))

    # Run monthly profit job
    results.append(("Run monthly profit job", post(client, token, "/api/elec/jobs/monthly-profit/run", {
        "month": "2024-06",
    })))

    # Check monthly profit
    results.append(("Query monthly profit", get(client, token, f"/api/elec/customer-monthly-profit/page?customer_account_id={customer_id}&page=1&page_size=20")))

    # Run monthly commission job
    results.append(("Run monthly commission job", post(client, token, "/api/elec/jobs/monthly-commission/run", {
        "month": "2024-06",
    })))

    # Check agent fee
    results.append(("Query agent fee", get(client, token, "/api/elec/agent-fee/page?page=1&page_size=20")))

    # Inquiry
    results.append(("Create inquiry", post(client, token, "/api/elec/inquiry/create", {
        "customer_id": customer_id,
        "inquiry_month": "2024-07",
        "expected_price": "0.3500",
    })))

    ok = [name for name, r in results if r["status"] in (200, 201)]
    fail = [(name, r["status"], r["json"]) for name, r in results if r["status"] not in (200, 201)]

    print(f"=== Business flow: {len(ok)}/{len(results)} passed ===")
    for name, r in results:
        status = "✅" if r["status"] in (200, 201) else "❌"
        print(f"{status} {name}: HTTP {r['status']}")

    if fail:
        print("\nFailures:")
        for name, code, detail in fail:
            print(f"  - {name}: {code} {detail}")

    with open("/tmp/elec-proxy-business-flow-report.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print("\nReport saved to /tmp/elec-proxy-business-flow-report.json")

    client.close()
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
