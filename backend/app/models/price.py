"""Price models."""

from datetime import date, time
from decimal import Decimal

from sqlalchemy import Integer, String, Numeric, Date, Time, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin


class BasePrice(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_base_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price_type: Mapped[int | None] = mapped_column(Integer)
    price_date: Mapped[date | None] = mapped_column(Date)
    hour_index: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    status: Mapped[int | None] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(Text)


class GridPrice(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_grid_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str | None] = mapped_column(String(7))
    time_period: Mapped[int | None] = mapped_column(Integer)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    price_coefficient: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    applicable_months: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[int | None] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(Text)


class WholesalePrice(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_wholesale_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price_date: Mapped[date | None] = mapped_column(Date)
    price_month: Mapped[str | None] = mapped_column(String(7))
    hour_index: Mapped[int | None] = mapped_column(Integer)
    time_period: Mapped[str | None] = mapped_column(String(10))
    wholesale_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    price_type: Mapped[int | None] = mapped_column(Integer)
    data_source: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[int | None] = mapped_column(Integer)
    remark: Mapped[str | None] = mapped_column(Text)


class MarketAllocationPrice(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_market_allocation_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str | None] = mapped_column(String(7))
    allocation_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    price_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[int | None] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(Text)


class OtherFee(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_other_fee"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month_config: Mapped[str | None] = mapped_column(String(7))
    distribution_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    government_fund: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    cross_subsidy: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    line_loss_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    status: Mapped[int | None] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(Text)
