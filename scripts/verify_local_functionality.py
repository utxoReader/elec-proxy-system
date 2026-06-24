#!/usr/bin/env python3
"""Local functional verification script for elec-proxy-system.

Runs against the real backend (localhost:8000) and frontend (localhost:5173)
to verify key business flows and API availability.
"""

import json
import sys
import httpx

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
TIMEOUT = 10.0


def log(message: str) -> None:
    print(message)


def check_health(client: httpx.Client) -> dict:
    r = client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    return {"name": "Health", "status": r.status_code == 200, "code": r.status_code, "detail": r.text[:200]}


def check_docs(client: httpx.Client) -> dict:
    r = client.get(f"{BASE_URL}/api/docs", timeout=TIMEOUT)
    return {"name": "Swagger Docs", "status": r.status_code == 200, "code": r.status_code, "detail": "available" if r.status_code == 200 else r.text[:200]}


def check_frontend(client: httpx.Client) -> dict:
    r = client.get(FRONTEND_URL, timeout=TIMEOUT)
    return {"name": "Frontend dev server", "status": r.status_code == 200, "code": r.status_code, "detail": "serving" if r.status_code == 200 else r.text[:200]}


def login(client: httpx.Client, username: str = "admin", password: str = "admin123") -> tuple[dict, str | None]:
    r = client.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": password}, timeout=TIMEOUT)
    token = None
    if r.status_code == 200:
        data = r.json().get("data") or {}
        token = data.get("access_token")
    return {"name": "Auth login", "status": r.status_code == 200 and token is not None and token != "placeholder-token", "code": r.status_code, "detail": data if r.status_code == 200 else r.text[:200]}, token


def authed_get(client: httpx.Client, token: str, path: str) -> httpx.Response:
    return client.get(f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)


def authed_post(client: httpx.Client, token: str, path: str, json_body: dict) -> httpx.Response:
    return client.post(f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {token}"}, json=json_body, timeout=TIMEOUT)


def check_module(client: httpx.Client, token: str, name: str, paths: list[tuple[str, str, dict | None]]) -> dict:
    """Check a module's endpoints. paths: list of (method, path, body_or_none)."""
    results = []
    for method, path, body in paths:
        try:
            if method == "GET":
                r = authed_get(client, token, path)
            else:
                r = authed_post(client, token, path, body or {})
            ok = r.status_code in (200, 201)
            results.append({"path": path, "method": method, "status": ok, "code": r.status_code, "detail": r.text[:120]})
        except Exception as e:
            results.append({"path": path, "method": method, "status": False, "code": 0, "detail": str(e)})
    all_ok = all(r["status"] for r in results)
    return {"name": name, "status": all_ok, "results": results}


def main() -> int:
    client = httpx.Client()
    report = []

    # Basic checks
    report.append(check_health(client))
    report.append(check_docs(client))
    report.append(check_frontend(client))

    # Auth
    auth_result, token = login(client)
    report.append(auth_result)

    if not token:
        log("Authentication failed; skipping business API checks.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    # Module checks
    modules = [
        ("Agent", [
            ("GET", "/api/elec/agent/page", None),
            ("GET", "/api/elec/agent/tree", None),
            ("POST", "/api/elec/agent/create", {"name": "Verify Agent", "type": 1, "status": 0, "tax_type": 1}),
        ]),
        ("Customer", [
            ("GET", "/api/elec/customer-account/page", None),
            ("POST", "/api/elec/customer-account/create", {
                "customer_name": "Verify Customer",
                "customer_status": 3,
                "price_difference": "0.050000",
                "contract_start_date": "2024-01-01",
                "contract_end_date": "2025-12-31",
            }),
        ]),
        ("Price", [
            ("GET", "/api/elec/base-price/page", None),
            ("GET", "/api/elec/grid-price/page", None),
            ("GET", "/api/elec/wholesale-price/page", None),
            ("GET", "/api/elec/market-allocation/page", None),
            ("GET", "/api/elec/other-fee/page", None),
        ]),
        ("Consumption", [
            ("GET", "/api/elec/daily-consumption/page", None),
            ("GET", "/api/elec/hourly-consumption/page", None),
            ("GET", "/api/elec/point96/page", None),
            ("GET", "/api/elec/usage-curve-template/page", None),
        ]),
        ("Inquiry", [
            ("GET", "/api/elec/inquiry/page", None),
            ("POST", "/api/elec/inquiry/create", {
                "customer_id": 1,
                "inquiry_month": "2024-06",
                "expected_price": "0.350000",
                "remark": "verify",
            }),
        ]),
        ("Profit", [
            ("GET", "/api/elec/customer-daily-profit/page", None),
            ("GET", "/api/elec/customer-monthly-profit/page", None),
        ]),
        ("Commission", [
            ("GET", "/api/elec/commission-config/page", None),
            ("GET", "/api/elec/agent-fee/page", None),
        ]),
        ("Scheduled Jobs", [
            ("POST", "/api/elec/jobs/daily-profit/run", {"date": "2024-06-01"}),
        ]),
    ]

    for name, paths in modules:
        report.append(check_module(client, token, name, paths))

    # Summary
    failed = [r for r in report if not r.get("status")]
    log(f"\n=== Summary: {len(report) - len(failed)}/{len(report)} checks passed ===")
    if failed:
        log("Failed checks:")
        for f in failed:
            log(f"  - {f['name']} (HTTP {f.get('code', '-')})")

    output_path = "/tmp/elec-proxy-functionality-report.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    log(f"\nFull report written to {output_path}")

    client.close()
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
