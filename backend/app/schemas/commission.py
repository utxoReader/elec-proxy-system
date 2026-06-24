"""Pydantic schemas for commission settlement."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ========== Commission Config ==========

class CommissionConfigCreate(BaseModel):
    effective_month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="生效月份 YYYY-MM")
    agent_commission_rate: Decimal = Field(..., max_digits=8, decimal_places=4, description="代理商分润比例(%)")
    parent_commission_rate: Optional[Decimal] = Field(None, max_digits=8, decimal_places=4, description="上级分润比例(%)")
    company_commission_rate: Optional[Decimal] = Field(None, max_digits=8, decimal_places=4, description="公司分润比例(%)")
    remark: Optional[str] = None


class CommissionConfigUpdate(BaseModel):
    id: int
    agent_commission_rate: Optional[Decimal] = None
    parent_commission_rate: Optional[Decimal] = None
    company_commission_rate: Optional[Decimal] = None
    remark: Optional[str] = None


class CommissionConfigResponse(BaseModel):
    id: int
    effective_month: str
    agent_commission_rate: Optional[Decimal] = None
    parent_commission_rate: Optional[Decimal] = None
    company_commission_rate: Optional[Decimal] = None
    status: Optional[int] = None
    remark: Optional[str] = None

    model_config = {"from_attributes": True}


# ========== Agent Fee ==========

class AgentFeeCreate(BaseModel):
    agent_id: int
    agent_name: Optional[str] = None
    customer_account_id: Optional[int] = None
    customer_name: Optional[str] = None
    fee_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    fee_type: int = Field(default=1, description="费用类型: 1=分润费用")
    customer_consumption: Optional[Decimal] = None
    customer_payment: Optional[Decimal] = None
    company_cost: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    tax_type: Optional[int] = None
    net_amount: Optional[Decimal] = None
    remark: Optional[str] = None


class AgentFeeUpdate(BaseModel):
    id: int
    commission_amount: Optional[Decimal] = None
    tax_type: Optional[int] = None
    net_amount: Optional[Decimal] = None
    remark: Optional[str] = None


class AgentFeeCalculate(BaseModel):
    agent_id: int
    fee_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class AgentFeeCalculatePreview(BaseModel):
    """Pure calculation preview without persistence."""
    agent_id: int
    fee_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class AgentFeeApproval(BaseModel):
    id: int
    approve_status: int = Field(..., description="2=approved, 3=rejected")
    approve_remark: Optional[str] = None


class AgentFeeBatchApproval(BaseModel):
    ids: list[int]
    approve_status: int = Field(..., description="2=approved, 3=rejected")
    approve_remark: Optional[str] = None


class AgentFeeBatchSettlement(BaseModel):
    ids: list[int]
    settlement_remark: Optional[str] = None


class AgentFeeResponse(BaseModel):
    id: int
    agent_id: int
    agent_name: Optional[str] = None
    customer_account_id: Optional[int] = None
    fee_month: str
    fee_type: Optional[int] = None
    gross_profit: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    tax_type: Optional[int] = None
    net_amount: Optional[Decimal] = None
    approve_status: Optional[int] = None
    settle_status: Optional[int] = None

    model_config = {"from_attributes": True}


class AgentFeeStatistics(BaseModel):
    total_amount: Decimal = Decimal("0")
    pending_approval_amount: Decimal = Decimal("0")
    approved_amount: Decimal = Decimal("0")
    settled_amount: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    count: int = 0
