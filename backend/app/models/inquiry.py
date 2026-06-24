"""Inquiry and quotation models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin


class Inquiry(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    """询价单表 - elec_inquiry"""
    __tablename__ = "elec_inquiry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inquiry_no: Mapped[str | None] = mapped_column(String(50), unique=True, comment="询价单号")
    agent_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="代理商ID")
    agent_name: Mapped[str | None] = mapped_column(String(100), comment="代理商名称")
    customer_name: Mapped[str | None] = mapped_column(String(100), comment="客户名称")
    contact_person: Mapped[str | None] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[str | None] = mapped_column(String(20), comment="联系电话")
    voltage_level: Mapped[str | None] = mapped_column(String(20), comment="电压等级")
    customer_type: Mapped[int | None] = mapped_column(Integer, comment="客户类型: 1=市场化, 2=国网代理")
    usage_month: Mapped[str | None] = mapped_column(String(7), comment="用电月份 YYYY-MM")
    estimated_monthly_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="预计月用电量 kWh")
    usage_address: Mapped[str | None] = mapped_column(String(200), comment="用电地址")
    industry_type: Mapped[str | None] = mapped_column(String(50), comment="行业类型")
    enterprise_feature: Mapped[str | None] = mapped_column(String(50))
    production_time: Mapped[str | None] = mapped_column(String(50))
    data_submit_type: Mapped[int | None] = mapped_column(Integer, comment="数据方式: 1=24h, 2=峰谷, 3=96点")
    peak_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    high_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    normal_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    valley_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    usage_curve_template_id: Mapped[int | None] = mapped_column(Integer)
    usage_curve_template_name: Mapped[str | None] = mapped_column(String(100))
    inquiry_status: Mapped[int | None] = mapped_column(Integer, default=1, comment="状态: 1=待处理, 2=已报价, 3=已接受, 4=已拒绝, 5=已过期, 6=已合作")
    is_second_inquiry: Mapped[int | None] = mapped_column(Integer, default=0)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    customer_confirm_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    admin_confirm_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cooperation_start_date: Mapped[date | None] = mapped_column(Date)
    cooperation_end_date: Mapped[date | None] = mapped_column(Date)
    terminate_date: Mapped[date | None] = mapped_column(Date)
    quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quote_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recommended_package_type: Mapped[int | None] = mapped_column(Integer, comment="推荐套餐: 1=一口价, 2=分时价")
    price_difference: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="价差 元/kWh")
    estimated_monthly_fee: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    estimated_savings: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    savings_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    remark: Mapped[str | None] = mapped_column(Text)
    consumption_data_json: Mapped[str | None] = mapped_column(Text)
    consumption_summary: Mapped[str | None] = mapped_column(Text)
