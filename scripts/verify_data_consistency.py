#!/usr/bin/env python3
"""
桐叶售电 — 数据一致性校验脚本

验证原 MySQL 数据库与新 PostgreSQL 数据库的业务数据一致性。
支持按表对比：记录数、关键数值字段 SUM、日期范围。

用法:
    python scripts/verify_data_consistency.py
    python scripts/verify_data_consistency.py --src mysql://user:pass@localhost:3306/elec
    python scripts/verify_data_consistency.py --tables elec_agent,elec_customer_account
"""

import argparse
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

# Default connection strings (update for your environment)
DEFAULT_SRC_URL = "mysql+pymysql://root:root@localhost:3306/elec_proxy"
DEFAULT_DST_URL = "postgresql+psycopg2://tongye:tongye@localhost:5432/tongye"


@dataclass
class TableCheck:
    """Table consistency check definition."""
    name: str
    key_fields: list[str] = field(default_factory=list)
    sum_fields: list[str] = field(default_factory=list)
    date_field: Optional[str] = None


# Tables to verify - add/remove as needed
TABLES_TO_CHECK = [
    TableCheck("elec_agent", key_fields=["id", "name"], sum_fields=[], date_field=None),
    TableCheck("elec_customer_account", key_fields=["id", "customer_name"], sum_fields=[], date_field="contract_start_date"),
    TableCheck("elec_base_price", key_fields=[], sum_fields=["price"], date_field="price_date"),
    TableCheck("elec_grid_price", key_fields=[], sum_fields=["base_price"], date_field=None),
    TableCheck("elec_wholesale_price", key_fields=[], sum_fields=["wholesale_price"], date_field="price_date"),
    TableCheck("elec_market_allocation_price", key_fields=[], sum_fields=["allocation_price"], date_field=None),
    TableCheck("elec_other_fee", key_fields=[], sum_fields=["distribution_price", "government_fund"], date_field=None),
    TableCheck("elec_customer_daily_consumption", key_fields=[], sum_fields=["total_consumption"], date_field="data_date"),
    TableCheck("elec_customer_hourly_consumption", key_fields=[], sum_fields=["consumption"], date_field="data_date"),
    TableCheck("elec_point96_data", key_fields=[], sum_fields=[], date_field="data_date"),
    TableCheck("elec_inquiry", key_fields=["id"], sum_fields=[], date_field="create_time"),
    TableCheck("elec_customer_daily_profit", key_fields=[], sum_fields=["total_profit", "retail_fee"], date_field="profit_date"),
    TableCheck("elec_customer_monthly_profit", key_fields=[], sum_fields=["total_profit", "adjusted_total_profit"], date_field=None),
    TableCheck("elec_agent_fee", key_fields=[], sum_fields=["commission_amount", "net_amount"], date_field=None),
    TableCheck("elec_commission_config", key_fields=[], sum_fields=["agent_commission_rate"], date_field=None),
]


def try_connect(url: str, label: str) -> Any:
    """Try to connect to database, return engine or None."""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(url)
        conn = engine.connect()
        conn.close()
        print(f"  ✅ {label} 连接成功")
        return engine
    except Exception as e:
        print(f"  ❌ {label} 连接失败: {e}")
        return None


def check_table(engine: Any, table: TableCheck) -> dict:
    """Run consistency checks on a single table."""
    result = {"name": table.name, "status": "ok", "checks": {}}

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # 1. Count records
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table.name}")).scalar()
            result["checks"]["record_count"] = count

            # 2. Check date range
            if table.date_field:
                range_result = conn.execute(
                    text(f"SELECT MIN({table.date_field}), MAX({table.date_field}) FROM {table.name}")
                ).first()
                result["checks"]["date_range"] = {
                    "min": str(range_result[0]) if range_result[0] else None,
                    "max": str(range_result[1]) if range_result[1] else None,
                }

            # 3. Sum numeric fields
            for field in table.sum_fields:
                val = conn.execute(text(f"SELECT COALESCE(SUM({field}), 0) FROM {table.name}")).scalar()
                result["checks"][f"sum_{field}"] = float(val) if val else 0

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def compare_results(src_result: dict, dst_result: dict) -> dict:
    """Compare src vs dst check results."""
    comparison = {
        "table": src_result["name"],
        "match": True,
        "differences": [],
    }

    if src_result["status"] == "error" or dst_result["status"] == "error":
        comparison["match"] = False
        comparison["differences"].append(f"查询失败: src={src_result.get('error')}, dst={dst_result.get('error')}")
        return comparison

    for key in src_result["checks"]:
        src_val = src_result["checks"][key]
        dst_val = dst_result["checks"].get(key)

        if key == "record_count":
            if src_val != dst_val:
                comparison["match"] = False
                comparison["differences"].append(f"{key}: src={src_val} vs dst={dst_val} (差异: {src_val - dst_val})")
        elif key.startswith("sum_"):
            diff = abs(src_val - dst_val)
            if diff > 0.01:  # tolerance for floating point
                comparison["match"] = False
                comparison["differences"].append(f"{key}: src={src_val:.2f} vs dst={dst_val:.2f} (差异: {diff:.2f})")
        elif key == "date_range":
            if src_val != dst_val:
                comparison["match"] = False
                comparison["differences"].append(f"{key}: src={src_val} vs dst={dst_val}")

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Verify data consistency between MySQL and PostgreSQL")
    parser.add_argument("--src", default=DEFAULT_SRC_URL, help="Source MySQL connection URL")
    parser.add_argument("--dst", default=DEFAULT_DST_URL, help="Destination PostgreSQL connection URL")
    parser.add_argument("--tables", default=None, help="Comma-separated table names to check (default: all)")
    args = parser.parse_args()

    print("=" * 60)
    print("桐叶售电 — 数据一致性校验")
    print("=" * 60)

    # Connect
    print("\n[连接数据库]")
    src = try_connect(args.src, "原系统(MySQL)")
    dst = try_connect(args.dst, "新系统(PostgreSQL)")

    if not src or not dst:
        print("\n❌ 数据库连接失败，无法执行校验")
        sys.exit(1)

    # Filter tables
    tables = TABLES_TO_CHECK
    if args.tables:
        table_names = set(args.tables.split(","))
        tables = [t for t in tables if t.name in table_names]
        missing = table_names - {t.name for t in tables}
        if missing:
            print(f"  ⚠️ 未找到表定义: {missing}")

    # Run checks
    print(f"\n[开始校验 {len(tables)} 张表]\n")
    all_match = True
    results = []

    for table in tables:
        print(f"  📋 {table.name}...", end=" ")
        src_result = check_table(src, table)
        dst_result = check_table(dst, table)
        comparison = compare_results(src_result, dst_result)
        results.append(comparison)

        if comparison["match"]:
            print("✅ 一致")
        else:
            print("❌ 不一致")
            for diff in comparison["differences"]:
                print(f"     ⚠️  {diff}")
            all_match = False

    # Summary
    print(f"\n{'=' * 60}")
    match_count = sum(1 for r in results if r["match"])
    print(f"结果: {match_count}/{len(results)} 张表一致")
    if all_match:
        print("✅ 全部一致！数据迁移验证通过。")
    else:
        print(f"❌ {len(results) - match_count} 张表存在差异，请检查详情。")

    # Print detailed table info
    print(f"\n{'=' * 60}")
    print("各表数据量:")
    print(f"{'表名':35s} {'原系统':>12s} {'新系统':>12s}")
    print("-" * 60)
    for table in tables:
        src_result = check_result_by_name(results, table.name, "src") if False else None
        print(f"{table.name:35s}")


if __name__ == "__main__":
    main()
