"""Pydantic schemas for inquiry and quotation management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InquiryCreate(BaseModel):
    """Schema for creating a new inquiry."""

    agent_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    voltage_level: Optional[str] = Field(None, max_length=20)
    customer_type: Optional[int] = Field(None, description="1=市场化, 2=国网代理")
    usage_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$", description="用电月份 YYYY-MM")
    estimated_monthly_consumption: Optional[Decimal] = Field(
        None, max_digits=16, decimal_places=4, description="预计月用电量 kWh"
    )
    usage_address: Optional[str] = Field(None, max_length=200)
    industry_type: Optional[str] = Field(None, max_length=50)
    enterprise_feature: Optional[str] = Field(None, max_length=50)
    production_time: Optional[str] = Field(None, max_length=50)
    data_submit_type: Optional[int] = Field(
        None, description="数据方式: 1=24h, 2=峰谷, 3=96点"
    )
    peak_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    high_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    normal_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    valley_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    usage_curve_template_id: Optional[int] = None
    remark: Optional[str] = None
    consumption_data_json: Optional[dict[str, Any]] = Field(
        None, description="24h/96-point consumption data as dict"
    )
    consumption_summary: Optional[str] = None
    region: Optional[str] = Field(None, max_length=20)

    model_config = ConfigDict(extra="ignore")


class InquiryUpdate(BaseModel):
    """Schema for updating basic inquiry info."""

    id: int
    agent_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    voltage_level: Optional[str] = Field(None, max_length=20)
    customer_type: Optional[int] = None
    usage_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    estimated_monthly_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    usage_address: Optional[str] = Field(None, max_length=200)
    industry_type: Optional[str] = Field(None, max_length=50)
    enterprise_feature: Optional[str] = Field(None, max_length=50)
    production_time: Optional[str] = Field(None, max_length=50)
    data_submit_type: Optional[int] = None
    peak_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    high_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    normal_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    valley_consumption: Optional[Decimal] = Field(None, max_digits=16, decimal_places=4)
    usage_curve_template_id: Optional[int] = None
    remark: Optional[str] = None
    consumption_data_json: Optional[dict[str, Any]] = None
    consumption_summary: Optional[str] = None
    region: Optional[str] = Field(None, max_length=20)

    model_config = ConfigDict(extra="ignore")


class InquiryOut(BaseModel):
    """Full output schema for an inquiry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inquiry_no: Optional[str] = None
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    customer_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    voltage_level: Optional[str] = None
    customer_type: Optional[int] = None
    usage_month: Optional[str] = None
    estimated_monthly_consumption: Optional[Decimal] = None
    usage_address: Optional[str] = None
    industry_type: Optional[str] = None
    enterprise_feature: Optional[str] = None
    production_time: Optional[str] = None
    data_submit_type: Optional[int] = None
    peak_consumption: Optional[Decimal] = None
    high_consumption: Optional[Decimal] = None
    normal_consumption: Optional[Decimal] = None
    valley_consumption: Optional[Decimal] = None
    usage_curve_template_id: Optional[int] = None
    usage_curve_template_name: Optional[str] = None
    inquiry_status: Optional[int] = None
    is_second_inquiry: Optional[int] = None
    reject_reason: Optional[str] = None
    customer_confirm_time: Optional[datetime] = None
    admin_confirm_time: Optional[datetime] = None
    cooperation_start_date: Optional[date] = None
    cooperation_end_date: Optional[date] = None
    terminate_date: Optional[date] = None
    quoted_at: Optional[datetime] = None
    quote_valid_until: Optional[datetime] = None
    recommended_package_type: Optional[int] = None
    price_difference: Optional[Decimal] = None
    estimated_monthly_fee: Optional[Decimal] = None
    estimated_savings: Optional[Decimal] = None
    savings_rate: Optional[Decimal] = None
    remark: Optional[str] = None
    consumption_data_json: Optional[dict[str, Any]] = None
    consumption_summary: Optional[str] = None
    region: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class InquiryPageOut(BaseModel):
    """Paginated list of inquiries."""

    list: list[InquiryOut]
    total: int
    pageNo: int
    pageSize: int


class QuotePayload(BaseModel):
    """Payload for submitting a quote."""

    price_difference: Decimal = Field(..., max_digits=10, decimal_places=6, description="价差 元/kWh")
    recommended_package_type: int = Field(..., description="1=一口价, 2=分时价")
    quote_valid_until: datetime = Field(..., description="报价有效期")
    estimated_monthly_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    estimated_savings: Decimal = Field(..., max_digits=16, decimal_places=4)
    savings_rate: Decimal = Field(..., max_digits=8, decimal_places=4)
    remark: Optional[str] = None


class RejectPayload(BaseModel):
    """Payload for rejecting an inquiry."""

    reject_reason: str


class StatusActionPayload(BaseModel):
    """Generic payload for accept/reject/cooperate/terminate actions."""

    reason: Optional[str] = None
    cooperation_start_date: Optional[date] = None
    cooperation_end_date: Optional[date] = None
    terminate_date: Optional[date] = None


class InquiryStatisticsOut(BaseModel):
    """Inquiry status statistics."""

    total: int
    pending: int
    quoted: int
    accepted: int
    rejected: int
    cooperated: int
    expired: int


class CalculatePricePayload(BaseModel):
    """Payload for dynamic price calculator."""

    package_type: int = Field(..., description="1=一口价, 2=分时价")
    estimated_consumption: Decimal = Field(..., max_digits=16, decimal_places=4)
    price_difference: Decimal = Field(..., max_digits=10, decimal_places=6)
    grid_price: Optional[Decimal] = Field(
        None, max_digits=10, decimal_places=6, description="平均电网价 元/kWh"
    )
    wholesale_prices: Optional[list[Decimal]] = Field(
        None, description="24小时批发价列表"
    )
    usage_curve_template_id: Optional[int] = None

    @field_validator("wholesale_prices")
    @classmethod
    def check_wholesale_prices(cls, v: Optional[list[Decimal]]) -> Optional[list[Decimal]]:
        if v is not None and len(v) != 24:
            raise ValueError("wholesale_prices must contain 24 values")
        return v


class CalculatePriceOut(BaseModel):
    """Output for dynamic price calculator."""

    estimated_monthly_fee: Decimal
    estimated_savings: Decimal
    savings_rate: Decimal
    remark: Optional[str] = None
