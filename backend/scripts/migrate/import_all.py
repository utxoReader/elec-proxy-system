"""Import exported JSON Lines data into PostgreSQL.

Usage:
    cd backend
    python scripts/migrate/import_all.py

Requires:
    - PostgreSQL running with the target database created
    - Alembic migrations run (tables exist)
    - Exported JSON Lines data in EXPORT_DATA_DIR
"""
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.config import settings

# Import all models so tables are registered
from app.models import *  # noqa: F401,F403


EXPORT_DATA_DIR = os.getenv("EXPORT_DATA_DIR", os.path.join("scripts", "export", "exported_data"))


# ========== Transform helpers ==========

def transform_deleted(row: dict) -> dict:
    """Convert old `deleted` boolean to new `deleted_at` timestamp."""
    if "deleted" in row:
        if row.get("deleted") in (1, True, "1"):
            row["deleted_at"] = datetime.now(timezone.utc).isoformat()
        del row["deleted"]
    return row


def transform_audit(row: dict) -> dict:
    """Map old audit fields to new ones."""
    if "create_time" in row:
        row["created_at"] = row.pop("create_time")
    if "update_time" in row:
        row["updated_at"] = row.pop("update_time")
    if "creator" in row:
        del row["creator"]  # Not used in new system
    if "updater" in row:
        del row["updater"]
    return row


def transform_tenant(row: dict) -> dict:
    """Map old tenant_id to region if present."""
    if "tenant_id" in row:
        # Default mapping - update as needed for actual tenant-to-region mapping
        del row["tenant_id"]
    return row


def transform_row(row: dict) -> dict:
    """Apply all transforms to a row."""
    row = transform_deleted(row)
    row = transform_audit(row)
    row = transform_tenant(row)
    return row


# ========== Import functions ==========

def get_table_model(table_name: str):
    """Get SQLAlchemy model class for a table name."""
    from app.database import Base
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, "__tablename__") and cls.__tablename__ == table_name:
            return cls
    return None


def clear_table(table_name: str):
    """Truncate a table before import."""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
        conn.commit()
    print(f"  Cleared table: {table_name}")


def import_table(table_name: str, data_dir: str) -> int:
    """Import data for one table from JSON Lines files."""
    table_dir = os.path.join(data_dir, table_name)
    if not os.path.isdir(table_dir):
        print(f"  ⚠️ No data directory for {table_name}")
        return 0

    # Find JSON Lines files
    jsonl_files = [f for f in os.listdir(table_dir) if f.endswith(".jsonl")]
    if not jsonl_files:
        print(f"  ⚠️ No JSON Lines files for {table_name}")
        return 0

    model = get_table_model(table_name)
    if not model:
        print(f"  ⚠️ No SQLAlchemy model found for {table_name}")
        return 0

    db = SessionLocal()
    imported = 0
    failed = 0
    skipped = 0

    try:
        for jsonl_file in sorted(jsonl_files):
            filepath = os.path.join(table_dir, jsonl_file)
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row_data = json.loads(line)
                        row_data = transform_row(row_data)

                        # Remove any keys that don't exist on the model
                        model_cols = {c.name for c in model.__table__.columns}
                        clean_data = {k: v for k, v in row_data.items()
                                      if k in model_cols}

                        instance = model(**clean_data)
                        db.add(instance)
                        imported += 1

                        # Batch commit every 500 rows
                        if imported % 500 == 0:
                            db.commit()
                            print(f"    {table_name}: {imported} rows...")
                    except Exception as e:
                        failed += 1
                        if failed <= 5:
                            print(f"    ❌ Row error: {e}")

            # Final commit per file
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"  ❌ Import error for {table_name}: {e}")
        raise
    finally:
        db.close()

    print(f"  ✅ {table_name}: {imported} imported, {failed} failed, {skipped} skipped")
    return imported


def import_all(data_dir: str = EXPORT_DATA_DIR):
    """Import all tables in dependency order."""
    print(f"[{datetime.now().isoformat()}] Starting data import")
    print(f"  Data directory: {data_dir}")

    if not os.path.isdir(data_dir):
        print(f"  ❌ Data directory not found: {data_dir}")
        print(f"  Please run export scripts first or set EXPORT_DATA_DIR")
        sys.exit(1)

    # Import order (dependency order)
    tables_order = [
        "elec_agent",
        "elec_commission_config",
        "elec_usage_curve_template",
        "elec_base_price",
        "elec_grid_price",
        "elec_wholesale_price",
        "elec_market_allocation_price",
        "elec_other_fee",
        "elec_customer_account",
        "elec_customer_account_price_history",
        "elec_inquiry",
        "elec_customer_daily_consumption",
        "elec_customer_hourly_consumption",
        "elec_point96_data",
        "elec_customer_daily_profit",
        "elec_customer_hourly_profit",
        "elec_customer_monthly_profit",
        "elec_agent_fee",
        "elec_import_task",
    ]

    results = {}
    total_start = datetime.now()

    for table in tables_order:
        print(f"\n--- Importing {table} ---")
        try:
            rows = import_table(table, data_dir)
            results[table] = {"rows": rows, "status": "OK"}
        except Exception as e:
            results[table] = {"rows": 0, "status": f"ERROR: {e}"}

    elapsed = (datetime.now() - total_start).total_seconds()

    print(f"\n{'='*50}")
    print(f"Import complete!")
    print(f"  Total tables: {len(results)}")
    print(f"  Total imported: {sum(r['rows'] for r in results.values())}")
    print(f"  Elapsed: {elapsed:.1f}s")

    # Print summary JSON
    summary = {
        "import_time": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "tables": results,
        "total_rows": sum(r["rows"] for r in results.values()),
    }
    summary_path = os.path.join(data_dir, "import_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    import_all()
