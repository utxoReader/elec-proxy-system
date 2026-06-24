# MySQL Data Export Scripts

Export data from the original elec-proxy-server MySQL database to JSON Lines format
for migration to the new PostgreSQL system.

## Prerequisites

- Python 3.12+
- `pymysql` package (`pip install pymysql`)
- Network access to the source MySQL database

## Usage

```bash
# Set MySQL connection info
export EXPORT_MYSQL_HOST="127.0.0.1"
export EXPORT_MYSQL_PORT="3306"
export EXPORT_MYSQL_USER="root"
export EXPORT_MYSQL_PASSWORD="your_password"
export EXPORT_MYSQL_DATABASE="elec_proxy"

# Set output directory (default: ./exported_data)
export EXPORT_OUTPUT_DIR="./exported_data"

# Optional: set date range for large tables
export EXPORT_DATE_FROM="2024-01-01"
export EXPORT_DATE_TO="2026-06-30"

# Optional: export only specific tables
export EXPORT_TABLES_ONLY="elec_agent,elec_customer_account"

# Run export
python scripts/export/export_all.py
```

## Output

Each table is exported to `{OUTPUT_DIR}/{table_name}/{table_name}_{timestamp}.jsonl`.

Format: JSON Lines (one JSON object per line).

A metadata file `export_summary.json` is generated with counts and timing.

## Tables Exported (in dependency order)

1. `elec_agent` — Agents
2. `elec_commission_config` — Commission config
3. `elec_usage_curve_template` — Usage curve templates
4. `elec_base_price` — Base electricity prices
5. `elec_grid_price` — Grid electricity prices
6. `elec_wholesale_price` — Wholesale prices
7. `elec_market_allocation_price` — Market allocation prices
8. `elec_other_fee` — Other fees
9. `elec_customer_account` — Customer accounts
10. `elec_customer_account_price_history` — Price history
11. `elec_inquiry` — Inquiries
12. `elec_customer_daily_consumption` — Daily consumption (24h)
13. `elec_customer_hourly_consumption` — Hourly consumption
14. `elec_point96_data` — 96-point data
15. `elec_customer_daily_profit` — Daily profit
16. `elec_customer_hourly_profit` — Hourly profit
17. `elec_customer_monthly_profit` — Monthly profit
18. `elec_agent_fee` — Agent fees
19. `elec_import_task` — Import tasks
