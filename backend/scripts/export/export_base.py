"""Base export class with MySQL connection, pagination, and file output."""
import json
import os
import time
from datetime import datetime
from typing import Any, Generator, Optional

import pymysql
from pymysql.cursors import DictCursor

from config import MySQLConfig, ExportConfig


class BaseExporter:
    """Base class for exporting MySQL tables to JSON Lines files."""

    def __init__(self, mysql_cfg: MySQLConfig, export_cfg: ExportConfig):
        self.mysql_cfg = mysql_cfg
        self.export_cfg = export_cfg
        self.connection: Optional[pymysql.Connection] = None
        self._total_rows = 0
        self._exported_rows = 0

    def connect(self) -> pymysql.Connection:
        """Create MySQL connection."""
        self.connection = pymysql.connect(
            host=self.mysql_cfg.host,
            port=self.mysql_cfg.port,
            user=self.mysql_cfg.user,
            password=self.mysql_cfg.password,
            database=self.mysql_cfg.database,
            charset=self.mysql_cfg.charset,
            cursorclass=DictCursor,
        )
        return self.connection

    def close(self):
        """Close MySQL connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def ensure_output_dir(self, table: str):
        """Create output directory for a table."""
        dir_path = os.path.join(self.export_cfg.output_dir, table)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @property
    def total_rows(self) -> int:
        return self._total_rows

    @property
    def exported_rows(self) -> int:
        return self._exported_rows

    def count_table(self, table: str, where_clause: str = "") -> int:
        """Count rows in a table."""
        sql = f"SELECT COUNT(*) AS cnt FROM `{table}`"
        if where_clause:
            sql += f" WHERE {where_clause}"
        with self.connection.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            return result["cnt"] if result else 0

    def fetch_page(self, table: str, page: int, page_size: int,
                   order_by: str = "id", where_clause: str = "") -> list[dict]:
        """Fetch a single page of data."""
        offset = (page - 1) * page_size
        sql = f"SELECT * FROM `{table}`"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += f" ORDER BY `{order_by}` LIMIT {page_size} OFFSET {offset}"
        with self.connection.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def serialize_value(self, value: Any) -> Any:
        """Convert MySQL values to JSON-serializable types."""
        if value is None:
            return None
        if isinstance(value, (datetime,)):
            return value.isoformat()
        if isinstance(value, (bytes, bytearray)):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, (str,)):
            return value
        # Decimal, other types - convert to string/float
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)

    def serialize_row(self, row: dict) -> dict:
        """Serialize a row to JSON-safe dict."""
        return {k: self.serialize_value(v) for k, v in row.items()}

    def export_table(self, table: str, order_by: str = "id",
                     where_clause: str = "", date_column: str = "") -> str:
        """Export a table to a JSON Lines file. Returns the output file path."""
        output_dir = self.ensure_output_dir(table)

        # If date_column is given, split export by date ranges for large tables
        if date_column and self.export_cfg.date_from and self.export_cfg.date_to:
            return self._export_by_date_range(
                table, order_by, where_clause, date_column, output_dir
            )

        return self._export_all_pages(table, order_by, where_clause, output_dir)

    def _export_all_pages(self, table: str, order_by: str,
                          where_clause: str, output_dir: str) -> str:
        """Export all rows from a table in pages."""
        total = self.count_table(table, where_clause)
        self._total_rows = total
        page_size = self.export_cfg.page_size
        total_pages = max(1, (total + page_size - 1) // page_size)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{table}_{timestamp}.jsonl"
        filepath = os.path.join(output_dir, filename)

        exported = 0
        with open(filepath, "w", encoding="utf-8") as f:
            for page in range(1, total_pages + 1):
                rows = self.fetch_page(table, page, page_size, order_by, where_clause)
                for row in rows:
                    f.write(json.dumps(self.serialize_row(row), ensure_ascii=False) + "\n")
                    exported += 1
                progress = min(100, int(exported / max(1, total) * 100))
                print(f"  [{table}] {exported}/{total} rows ({progress}%)")

        self._exported_rows = exported

        # Write metadata
        meta = {
            "table": table,
            "total_rows": total,
            "exported_rows": exported,
            "export_time": timestamp,
            "file": filename,
            "where_clause": where_clause or None,
            "page_size": page_size,
        }
        with open(os.path.join(output_dir, f"{table}_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        return filepath

    def _export_by_date_range(self, table: str, order_by: str,
                               where_clause: str, date_column: str,
                               output_dir: str) -> str:
        """Export large tables split by date ranges."""
        from datetime import datetime as dt
        date_from = dt.fromisoformat(self.export_cfg.date_from) if self.export_cfg.date_from else None
        date_to = dt.fromisoformat(self.export_cfg.date_to) if self.export_cfg.date_to else None

        clause_parts = []
        if where_clause:
            clause_parts.append(where_clause)
        if date_from:
            clause_parts.append(f"`{date_column}` >= '{date_from.strftime('%Y-%m-%d')}'")
        if date_to:
            clause_parts.append(f"`{date_column}` <= '{date_to.strftime('%Y-%m-%d')}'")

        combined_where = " AND ".join(clause_parts) if clause_parts else ""
        return self._export_all_pages(table, order_by, combined_where, output_dir)
