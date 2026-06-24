"""Pydantic schemas for agent management."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ============ Agent ============
class AgentCreate(BaseModel):
    name: str = Field(..., max_length=100)
    type: Optional[int] = Field(None, description="1=大代理商, 2=小代理商")
    parent_id: Optional[int] = None
    status: Optional[int] = Field(0)
    tax_type: Optional[int] = Field(None, description="1=专票13%, 2=专票6%, 3=普票, 4=没票")
    remark: Optional[str] = None


class AgentUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    type: Optional[int] = None
    parent_id: Optional[int] = None
    status: Optional[int] = None
    tax_type: Optional[int] = None
    remark: Optional[str] = None


class AgentTreeNode(BaseModel):
    id: int
    name: str
    type: Optional[int] = None
    parent_id: Optional[int] = None
    status: Optional[int] = None
    children: list["AgentTreeNode"] = []


# ============ CommissionConfig ============
class CommissionConfigCreate(BaseModel):
    config_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    effective_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    agent_commission_rate: Optional[Decimal] = Field(None, max_digits=8, decimal_places=4)
    parent_commission_rate: Optional[Decimal] = Field(None, max_digits=8, decimal_places=4)
    company_commission_rate: Optional[Decimal] = Field(None, max_digits=8, decimal_places=4)
    remark: Optional[str] = None


class CommissionConfigUpdate(BaseModel):
    id: int
    config_month: Optional[str] = None
    effective_month: Optional[str] = None
    agent_commission_rate: Optional[Decimal] = None
    parent_commission_rate: Optional[Decimal] = None
    company_commission_rate: Optional[Decimal] = None
    remark: Optional[str] = None


# ============ AgentFee ============
class AgentFeeBatchSettle(BaseModel):
    ids: list[int]
    settlement_status: int = Field(..., description="2=已结算, 3=已支付")


class AgentFeeReverseSettle(BaseModel):
    ids: list[int]
