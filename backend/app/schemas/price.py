"""Pydantic schemas for price management."""
from datetime import date, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class BasePriceCreate(BaseModel):
    price_type: int = Field(..., description="价格类型: 1=月度基准价")
    price_date: date = Field(..., description="价格日期")
    hour_index: int = Field(..., ge=0, le=23, description="小时索引 0-23")
    price: Decimal = Field(..., max_digits=10, decimal_places=6, description="价格 元/度")
    status: Optional[int] = Field(0, description="状态: 0=启用, 1=禁用")
    remark: Optional[str] = None


class BasePriceUpdate(BaseModel):
    id: int
    price_type: Optional[int] = None
    price_date: Optional[date] = None
    hour_index: Optional[int] = None
    price: Optional[Decimal] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class GridPriceCreate(BaseModel):
    year_month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="年月 YYYY-MM")
    time_period: int = Field(..., description="时段: 1=尖峰, 2=高峰, 3=平时, 4=低谷")
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    base_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    price_coefficient: Optional[Decimal] = None
    applicable_months: Optional[str] = None
    status: Optional[int] = Field(0)
    remark: Optional[str] = None


class GridPriceUpdate(BaseModel):
    id: int
    year_month: Optional[str] = None
    time_period: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    base_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    price_coefficient: Optional[Decimal] = None
    applicable_months: Optional[str] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class WholesalePriceCreate(BaseModel):
    price_date: date
    price_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    hour_index: int = Field(..., ge=0, le=23)
    time_period: str = Field(..., description="时段名称: 尖峰/峰/平/谷")
    wholesale_price: Optional[Decimal] = None
    price_type: Optional[int] = None
    data_source: Optional[int] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class WholesalePriceUpdate(BaseModel):
    id: int
    price_date: Optional[date] = None
    price_month: Optional[str] = None
    hour_index: Optional[int] = None
    time_period: Optional[str] = None
    wholesale_price: Optional[Decimal] = None
    price_type: Optional[int] = None
    data_source: Optional[int] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class MarketAllocationCreate(BaseModel):
    year_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    allocation_price: Optional[Decimal] = None
    price_date: Optional[date] = None
    status: Optional[int] = Field(0)
    remark: Optional[str] = None


class MarketAllocationUpdate(BaseModel):
    id: int
    year_month: Optional[str] = None
    allocation_price: Optional[Decimal] = None
    price_date: Optional[date] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class OtherFeeCreate(BaseModel):
    month_config: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    distribution_price: Optional[Decimal] = None
    government_fund: Optional[Decimal] = None
    cross_subsidy: Optional[Decimal] = None
    line_loss_fee: Optional[Decimal] = None
    status: Optional[int] = Field(0)
    remark: Optional[str] = None


class OtherFeeUpdate(BaseModel):
    id: int
    month_config: Optional[str] = None
    distribution_price: Optional[Decimal] = None
    government_fund: Optional[Decimal] = None
    cross_subsidy: Optional[Decimal] = None
    line_loss_fee: Optional[Decimal] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageResult(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
