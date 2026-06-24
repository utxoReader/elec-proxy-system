"""Consumption data models."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, String, Numeric, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin


class CustomerDailyConsumption(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_customer_daily_consumption"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int | None] = mapped_column(Integer, index=True)
    inquiry_id: Mapped[int | None] = mapped_column(Integer)
    customer_name: Mapped[str | None] = mapped_column(String(100))
    account_number: Mapped[str | None] = mapped_column(String(50))
    data_date: Mapped[date | None] = mapped_column(Date)
    data_month: Mapped[str | None] = mapped_column(String(7))
    # 24 hour columns
    hour_00: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_01: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_02: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_03: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_04: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_05: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_06: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_07: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_08: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_09: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_10: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_11: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_12: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_13: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_14: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_15: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_16: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_17: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_18: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_19: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_21: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_22: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    hour_23: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    total_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    peak_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    high_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    normal_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    valley_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    data_type: Mapped[int | None] = mapped_column(Integer, default=1)
    data_source: Mapped[int | None] = mapped_column(Integer, default=1)
    package_type: Mapped[int | None] = mapped_column(Integer)
    price_difference: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    import_file_name: Mapped[str | None] = mapped_column(String(200))
    import_batch_id: Mapped[str | None] = mapped_column(String(50))
    raw_data_count: Mapped[int | None] = mapped_column(Integer)
    remarks: Mapped[str | None] = mapped_column(Text)
    commission_status: Mapped[int | None] = mapped_column(Integer, default=1)
    data_locked: Mapped[bool | None] = mapped_column(Boolean, default=False)
    commission_calculated_time: Mapped[date | None] = mapped_column(Date)


class CustomerHourlyConsumption(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_customer_hourly_consumption"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int | None] = mapped_column(Integer, index=True)
    inquiry_id: Mapped[int | None] = mapped_column(Integer)
    customer_name: Mapped[str | None] = mapped_column(String(100))
    data_date: Mapped[date | None] = mapped_column(Date)
    data_month: Mapped[str | None] = mapped_column(String(7))
    hour_index: Mapped[int | None] = mapped_column(Integer)
    consumption: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    time_period: Mapped[int | None] = mapped_column(Integer)
    data_type: Mapped[int | None] = mapped_column(Integer, default=1)
    data_source: Mapped[int | None] = mapped_column(Integer, default=1)
    package_type: Mapped[int | None] = mapped_column(Integer)
    retail_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    delivered_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    wholesale_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    remarks: Mapped[str | None] = mapped_column(Text)


class Point96Data(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_point96_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int | None] = mapped_column(Integer, index=True)
    market_member_name: Mapped[str | None] = mapped_column(String(100))
    account_number: Mapped[str | None] = mapped_column(String(50))
    measure_point: Mapped[str | None] = mapped_column(String(50))
    data_date: Mapped[date | None] = mapped_column(Date)
    is_contracted: Mapped[bool | None] = mapped_column(Boolean)
    trading_unit_name: Mapped[str | None] = mapped_column(String(100))
    total_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    # 96 points abbreviated - full set in migration
    p0015: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0030: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0045: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0100: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0115: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0130: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0145: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0200: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0215: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0230: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0245: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0300: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0315: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0330: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0345: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    p0400: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    batch_no: Mapped[str | None] = mapped_column(String(50))
    processed: Mapped[int | None] = mapped_column(Integer, default=0)
    convert_time: Mapped[date | None] = mapped_column(Date)
