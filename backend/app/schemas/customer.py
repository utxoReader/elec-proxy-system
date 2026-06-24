"""Pydantic schemas for customer management."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CustomerAccountCreate(BaseModel):
    customer_name: str = Field(..., max_length=100)
    customer_status: Optional[int] = Field(2, description="1=待注册, 2=待签约, 3=已签约, 4=已终止")
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    voltage_level: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    account_number: Optional[str] = None
    service_password: Optional[str] = None
    verification_code: Optional[str] = None
    trading_center_account: Optional[str] = None
    trading_center_password: Optional[str] = None
    package_type: Optional[int] = Field(None, description="1=一口价, 2=分时价")
    price_difference: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6)
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    industry_type: Optional[str] = None
    enterprise_feature: Optional[str] = None
    production_time: Optional[str] = None
    credit_code: Optional[str] = None
    legal_person: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    remark: Optional[str] = None


class CustomerAccountUpdate(BaseModel):
    id: int
    customer_name: Optional[str] = None
    customer_status: Optional[int] = None
    agent_id: Optional[int] = None
    voltage_level: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    package_type: Optional[int] = None
    price_difference: Optional[Decimal] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    industry_type: Optional[str] = None
    remark: Optional[str] = None


class CustomerPriceChange(BaseModel):
    customer_account_id: int
    new_price_difference: Decimal = Field(..., max_digits=10, decimal_places=6)
    effective_date: date = Field(..., description="生效日期(次月1日)")
    change_reason: Optional[str] = None
    new_contract_start_date: Optional[date] = None
    new_contract_end_date: Optional[date] = None


class CustomerStatusChange(BaseModel):
    id: int
    customer_status: int = Field(..., description="目标状态")
