"""Agent and agent fee models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin


class Agent(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    """代理商信息表 - elec_agent (also used as auth user table)"""
    __tablename__ = "elec_agent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="代理商名称/用户名")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="bcrypt 密码哈希")
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="agent", comment="系统角色: admin/agent")
    type: Mapped[int | None] = mapped_column(Integer, comment="类型: 1=大代理商, 2=小代理商")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="上级代理商ID")
    status: Mapped[int | None] = mapped_column(Integer, default=0, comment="状态: 0=启用, 1=禁用")
    tax_type: Mapped[int | None] = mapped_column(Integer, comment="税率类型: 1=专票13%, 2=专票6%, 3=普票, 4=没票")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")


class AgentFee(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    """代理费/佣金表 - elec_agent_fee"""
    __tablename__ = "elec_agent_fee"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="代理商ID")
    agent_name: Mapped[str | None] = mapped_column(String(100), comment="代理商名称")
    customer_account_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="客户账户ID")
    customer_name: Mapped[str | None] = mapped_column(String(100), comment="客户名称")
    fee_month: Mapped[str | None] = mapped_column(String(7), comment="费用月份 YYYY-MM")
    config_month: Mapped[str | None] = mapped_column(String(7), comment="配置月份 YYYY-MM")
    fee_date: Mapped[date | None] = mapped_column(Date, comment="费用日期")
    customer_consumption: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="用电量 kWh")
    customer_payment: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="客户支付额 元")
    company_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="公司成本 元")
    gross_profit: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="毛利润 元")
    commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="佣金比例")
    commission_amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="佣金金额 元")
    fee_type: Mapped[int | None] = mapped_column(Integer, comment="费用类型: 1=销售分润, 2=服务费, 3=奖励, 4=其他")
    tax_type: Mapped[int | None] = mapped_column(Integer, comment="税率类型")
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="税率")
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="税费 元")
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), comment="净额 元")
    settlement_status: Mapped[int | None] = mapped_column(Integer, default=1, comment="结算状态: 1=待结算, 2=已结算, 3=已支付, 4=已取消")
    settlement_date: Mapped[date | None] = mapped_column(Date, comment="结算日期")
    payment_date: Mapped[date | None] = mapped_column(Date, comment="支付日期")
    payment_method: Mapped[int | None] = mapped_column(Integer, comment="支付方式: 1=银行转账, 2=现金, 3=支票, 4=其他")
    payment_voucher: Mapped[str | None] = mapped_column(String(200), comment="支付凭证")
    approval_status: Mapped[int | None] = mapped_column(Integer, default=1, comment="审批状态: 1=待审核, 2=已审核, 3=已驳回")
    approver_id: Mapped[int | None] = mapped_column(Integer, comment="审批人ID")
    approver_name: Mapped[str | None] = mapped_column(String(50), comment="审批人名称")
    approval_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="审批时间")
    approval_comment: Mapped[str | None] = mapped_column(Text, comment="审批意见")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")
