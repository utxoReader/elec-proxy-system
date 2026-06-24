"""Export configuration.

Update these values to match the source MySQL database.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MySQLConfig:
    host: str = field(default_factory=lambda: os.getenv("EXPORT_MYSQL_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("EXPORT_MYSQL_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("EXPORT_MYSQL_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("EXPORT_MYSQL_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("EXPORT_MYSQL_DATABASE", "elec_proxy"))
    charset: str = "utf8mb4"


@dataclass
class ExportConfig:
    output_dir: str = field(default_factory=lambda: os.getenv("EXPORT_OUTPUT_DIR", "./exported_data"))
    page_size: int = field(default_factory=lambda: int(os.getenv("EXPORT_PAGE_SIZE", "1000")))
    date_from: Optional[str] = field(default_factory=lambda: os.getenv("EXPORT_DATE_FROM"))
    date_to: Optional[str] = field(default_factory=lambda: os.getenv("EXPORT_DATE_TO"))
    # Set to specific tables to export only those, e.g. "elec_agent,elec_customer_account"
    tables_only: Optional[str] = field(default_factory=lambda: os.getenv("EXPORT_TABLES_ONLY"))
    # Export as individual JSON files per row (default: JSON Lines batch file)
    single_file: bool = field(default_factory=lambda: os.getenv("EXPORT_SINGLE_FILE", "true").lower() == "true")
