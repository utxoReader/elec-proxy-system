"""Export all tables in dependency order."""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MySQLConfig, ExportConfig
from export_base import BaseExporter


def export_all():
    """Main export entry point - exports all tables in dependency order."""
    mysql_cfg = MySQLConfig()
    export_cfg = ExportConfig()

    print(f"[{datetime.now().isoformat()}] Starting MySQL data export")
    print(f"  MySQL: {mysql_cfg.user}@{mysql_cfg.host}:{mysql_cfg.port}/{mysql_cfg.database}")
    print(f"  Output: {export_cfg.output_dir}")
    print(f"  Page size: {export_cfg.page_size}")
    if export_cfg.date_from:
        print(f"  Date range: {export_cfg.date_from} ~ {export_cfg.date_to}")

    os.makedirs(export_cfg.output_dir, exist_ok=True)
    exporter = BaseExporter(mysql_cfg, export_cfg)
    exporter.connect()

    # Tables in dependency order (no FK → has FK)
    table_configs = [
        # No dependencies
        ("elec_agent", "id", "", ""),
        ("elec_commission_config", "id", "", ""),
        ("elec_usage_curve_template", "id", "", ""),
        ("elec_base_price", "id", "", "price_date"),
        ("elec_grid_price", "id", "", "year_month"),
        ("elec_wholesale_price", "id", "", "price_date"),
        ("elec_market_allocation_price", "id", "", ""),
        ("elec_other_fee", "id", "", ""),
        # Depends on agent
        ("elec_customer_account", "id", "", ""),
        ("elec_customer_account_price_history", "id", "", ""),
        # Depends on agent + customer_account
        ("elec_inquiry", "id", "", ""),
        # Large data tables (date-filtered)
        ("elec_customer_daily_consumption", "id", "", "data_date"),
        ("elec_customer_hourly_consumption", "id", "", "data_date"),
        ("elec_point96_data", "id", "", "data_date"),
        # Profit tables
        ("elec_customer_daily_profit", "id", "", "profit_date"),
        ("elec_customer_hourly_profit", "id", "", "profit_date"),
        ("elec_customer_monthly_profit", "id", "", ""),
        # Agent fees
        ("elec_agent_fee", "id", "", ""),
        # Import tasks
        ("elec_import_task", "id", "", ""),
    ]

    results = {}
    total_start = datetime.now()

    for table, order_by, where, date_col in table_configs:
        if export_cfg.tables_only and table not in export_cfg.tables_only:
            continue

        print(f"\n--- Exporting {table} ---")
        try:
            filepath = exporter.export_table(table, order_by, where, date_col)
            results[table] = {
                "rows": exporter.exported_rows,
                "file": filepath,
                "status": "OK",
            }
            print(f"  ✅ {table}: {exporter.exported_rows} rows -> {filepath}")
        except Exception as e:
            results[table] = {"rows": 0, "file": "", "status": f"ERROR: {e}"}
            print(f"  ❌ {table}: ERROR - {e}")

    exporter.close()

    # Write summary
    elapsed = (datetime.now() - total_start).total_seconds()
    summary = {
        "export_time": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "tables": results,
        "total_rows": sum(r["rows"] for r in results.values()),
    }
    summary_path = os.path.join(export_cfg.output_dir, "export_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Export complete!")
    print(f"  Total tables: {len(results)}")
    print(f"  Total rows: {summary['total_rows']}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    export_all()
