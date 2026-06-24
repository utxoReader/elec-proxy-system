"""Customer account models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin


class CustomerAccount(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    """客户账户表 - elec_customer_account"""
    __tablename__ = "elec_customer_account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_status: Mapped[int | None] = mapped_column(Integer, comment="状态: 1=待注册, 2=待签约, 3=已签约, 4=已终止")
    agent_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="代理商ID")
    agent_name: Mapped[str | None] = mapped_column(String(100), comment="代理商名称")
    customer_name: Mapped[str | None] = mapped_column(String(100), comment="客户名称")
    inquiry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="询价时间")
    voltage_level: Mapped[str | None] = mapped_column(String(20), comment="电压等级")
    account_number: Mapped[str | None] = mapped_column(String(500), comment="户号(逗号分隔)")
    service_password: Mapped[str | None] = mapped_column(String(100), comment="服务密码")
    verification_code: Mapped[str | None] = mapped_column(String(50), comment="验证码")
    contact_phone: Mapped[str | None] = mapped_column(String(20), comment="联系电话")
    contact_person: Mapped[str | None] = mapped_column(String(50), comment="联系人")
    trading_center_account: Mapped[str | None] = mapped_column(String(100), comment="交易中心账号")
    trading_center_password: Mapped[str | None] = mapped_column(String(100), comment="交易中心密码")
    package_type: Mapped[int | None] = mapped_column(Integer, comment="套餐类型: 1=一口价, 2=分时价")
    price_difference: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="价差 元/kWh")
    contract_start_date: Mapped[date | None] = mapped_column(Date, comment="合同开始日期")
    contract_end_date: Mapped[date | None] = mapped_column(Date, comment="合同结束日期")
    industry_type: Mapped[str | None] = mapped_column(String(50), comment="行业类型")
    enterprise_feature: Mapped[str | None] = mapped_column(String(50), comment="企业特征")
    production_time: Mapped[str | None] = mapped_column(String(50), comment="生产时间")
    credit_code: Mapped[str | None] = mapped_column(String(50), comment="统一社会信用代码")
    legal_person: Mapped[str | None] = mapped_column(String(50), comment="法人代表")
    email: Mapped[str | None] = mapped_column(String(100), comment="邮箱")
    address: Mapped[str | None] = mapped_column(String(200), comment="地址")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")


class CustomerAccountPriceHistory(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    """客户账户价差历史表 - elec_customer_account_price_history"""
    __tablename__ = "elec_customer_account_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="客户账户ID")
    customer_name: Mapped[str | None] = mapped_column(String(100), comment="客户名称")
    old_price_difference: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="旧价差")
    new_price_difference: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="新价差")
    old_contract_start_date: Mapped[date | None] = mapped_column(Date)
    old_contract_end_date: Mapped[date | None] = mapped_column(Date)
    new_contract_start_date: Mapped[date | None] = mapped_column(Date)
    new_contract_end_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date, comment="生效日期(次月1日)")
    change_reason: Mapped[str | None] = mapped_column(Text, comment="变更原因")
    change_type: Mapped[int | None] = mapped_column(Integer, comment="变更类型: 1=价差, 2=合同时间, 3=两者")
    status: Mapped[int | None] = mapped_column(Integer, default=1, comment="状态: 1=待生效, 2=已生效, 3=已取消")
