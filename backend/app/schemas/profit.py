"""Pydantic schemas for profit calculation."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ========== Hourly Profit ==========

class HourlyProfitQuery(BaseModel):
    customer_id: int
    profit_date: Optional[date] = None
    profit_month: Optional[str] = None  # YYYY-MM


class HourlyProfitResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    profit_date: date
    profit_month: str
    hour: int
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    time_period: Optional[int] = None
    time_period_name: Optional[str] = None
    consumption: Optional[Decimal] = None
    retail_unit_price: Optional[Decimal] = None
    wholesale_unit_price: Optional[Decimal] = None
    retail_fee: Optional[Decimal] = None
    wholesale_fee: Optional[Decimal] = None
    market_allocation_fee: Optional[Decimal] = None
    profit: Optional[Decimal] = None

    model_config = {"from_attributes": True}


# ========== Daily Profit ==========

class BatchDateRange(BaseModel):
    start_date: date
    end_date: date


class DailyProfitPageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    customer_id: Optional[int] = None
    agent_id: Optional[int] = None
    profit_date: Optional[str] = None  # YYYY-MM-DD
    profit_month: Optional[str] = None  # YYYY-MM
    status: Optional[int] = None


class DailyProfitCreate(BaseModel):
    customer_id: int
    profit_date: date
    total_consumption: Decimal = Field(..., max_digits=16, decimal_places=4)
    retail_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    wholesale_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    market_allocation_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    total_profit: Decimal = Field(..., max_digits=16, decimal_places=4)
    price_difference: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6)


class DailyProfitCalculateQuery(BaseModel):
    customer_account_id: int
    date: date


class DailyProfitResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    profit_date: date
    profit_month: str
    agent_id: Optional[int] = None
    total_consumption: Optional[Decimal] = None
    retail_fee: Optional[Decimal] = None
    wholesale_fee: Optional[Decimal] = None
    market_allocation_fee: Optional[Decimal] = None
    total_profit: Optional[Decimal] = None
    agent_commission_amount: Optional[Decimal] = None
    company_commission_amount: Optional[Decimal] = None
    status: Optional[int] = None

    model_config = {"from_attributes": True}


# ========== Monthly Profit ==========

class MonthlyProfitPageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    customer_id: Optional[int] = None
    agent_id: Optional[int] = None
    profit_month: Optional[str] = None  # YYYY-MM
    status: Optional[int] = None


class MonthlyProfitCreate(BaseModel):
    customer_id: int
    profit_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    total_consumption: Decimal = Field(..., max_digits=16, decimal_places=4)
    retail_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    wholesale_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    market_allocation_fee: Decimal = Field(..., max_digits=16, decimal_places=4)
    total_profit: Decimal = Field(..., max_digits=16, decimal_places=4)


class MonthlyProfitUpdate(BaseModel):
    id: int
    total_consumption: Optional[Decimal] = None
    retail_fee: Optional[Decimal] = None
    wholesale_fee: Optional[Decimal] = None
    market_allocation_fee: Optional[Decimal] = None
    total_profit: Optional[Decimal] = None
    remark: Optional[str] = None


class MonthlyProfitAdjustment(BaseModel):
    id: int
    adjustment_consumption: Decimal = Field(..., description="调平电量(可正可负)")
    adjustment_remark: Optional[str] = None


class MonthlyProfitConfirm(BaseModel):
    ids: list[int]
    confirm_remark: Optional[str] = None


class MonthlyProfitSettlement(BaseModel):
    id: int
    settlement_remark: Optional[str] = None


class MonthlyProfitBatchGenerate(BaseModel):
    profit_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class MonthlyProfitRecalculate(BaseModel):
    ids: list[int]


class MonthlyProfitAgentFeesGenerate(BaseModel):
    profit_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    agent_ids: Optional[list[int]] = None


class MonthlyProfitResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    profit_month: str
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    total_consumption: Optional[Decimal] = None
    retail_fee: Optional[Decimal] = None
    wholesale_fee: Optional[Decimal] = None
    market_allocation_fee: Optional[Decimal] = None
    total_profit: Optional[Decimal] = None
    adjusted_total_profit: Optional[Decimal] = None
    status: Optional[int] = None
    adjustment_status: Optional[int] = None
    settlement_status: Optional[int] = None
    data_completeness_rate: Optional[Decimal] = None
    data_days_count: Optional[int] = None
    expected_days_count: Optional[int] = None

    model_config = {"from_attributes": True}
