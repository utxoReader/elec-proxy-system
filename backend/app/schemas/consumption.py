"""Pydantic schemas for electricity consumption data."""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HourData = dict[str, Decimal]
Point96Dict = dict[str, Decimal]


def _validate_hour_keys(value: HourData | None) -> HourData | None:
    """Ensure hour keys follow hour_00..hour_23 pattern."""
    if value is None:
        return value
    for key in value:
        if not (key.startswith("hour_") and len(key) == 7 and key[5:].isdigit()):
            raise ValueError(f"Invalid hour key: {key}")
        idx = int(key[5:])
        if idx < 0 or idx > 23:
            raise ValueError(f"Hour index must be 0-23: {key}")
    return value


def _validate_point_keys(value: Point96Dict | None) -> Point96Dict | None:
    """Ensure 96-point keys follow HH:MM pattern."""
    if value is None:
        return value
    for key in value:
        parts = key.split(":")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError(f"Invalid point key: {key}, expected HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and minute in (15, 30, 45, 0)):
            raise ValueError(f"Invalid point key: {key}")
    return value


# ---------------------------------------------------------------------------
# CustomerDailyConsumption
# ---------------------------------------------------------------------------

class CustomerDailyConsumptionBase(BaseModel):
    """Common fields for daily consumption."""

    customer_account_id: Optional[int] = None
    inquiry_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    data_date: Optional[date] = None
    data_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    hours: Optional[HourData] = Field(default_factory=dict, description="24小时电量 {hour_00..hour_23}")
    total_consumption: Optional[Decimal] = None
    peak_consumption: Optional[Decimal] = None
    high_consumption: Optional[Decimal] = None
    normal_consumption: Optional[Decimal] = None
    valley_consumption: Optional[Decimal] = None
    data_type: Optional[int] = Field(1, description="数据类型")
    data_source: Optional[int] = Field(1, description="数据来源")
    package_type: Optional[int] = None
    price_difference: Optional[Decimal] = None
    import_file_name: Optional[str] = Field(None, max_length=200)
    import_batch_id: Optional[str] = Field(None, max_length=50)
    raw_data_count: Optional[int] = None
    remarks: Optional[str] = None
    commission_status: Optional[int] = Field(1)
    data_locked: Optional[bool] = False
    commission_calculated_time: Optional[date] = None
    region: Optional[str] = Field(None, max_length=20)

    @field_validator("hours")
    @classmethod
    def check_hours(cls, v: HourData | None) -> HourData | None:
        return _validate_hour_keys(v)


class CustomerDailyConsumptionCreate(CustomerDailyConsumptionBase):
    """Create schema."""

    pass


class CustomerDailyConsumptionUpdate(BaseModel):
    """Update schema (all fields optional)."""

    id: int
    customer_account_id: Optional[int] = None
    inquiry_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    data_date: Optional[date] = None
    data_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    hours: Optional[HourData] = Field(None, description="24小时电量 {hour_00..hour_23}")
    total_consumption: Optional[Decimal] = None
    peak_consumption: Optional[Decimal] = None
    high_consumption: Optional[Decimal] = None
    normal_consumption: Optional[Decimal] = None
    valley_consumption: Optional[Decimal] = None
    data_type: Optional[int] = None
    data_source: Optional[int] = None
    package_type: Optional[int] = None
    price_difference: Optional[Decimal] = None
    import_file_name: Optional[str] = Field(None, max_length=200)
    import_batch_id: Optional[str] = Field(None, max_length=50)
    raw_data_count: Optional[int] = None
    remarks: Optional[str] = None
    commission_status: Optional[int] = None
    data_locked: Optional[bool] = None
    commission_calculated_time: Optional[date] = None
    region: Optional[str] = Field(None, max_length=20)

    @field_validator("hours")
    @classmethod
    def check_hours(cls, v: HourData | None) -> HourData | None:
        return _validate_hour_keys(v)


class CustomerDailyConsumptionOut(CustomerDailyConsumptionBase):
    """Output schema."""

    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class CustomerDailyConsumptionPageOut(BaseModel):
    """Paginated output matching `paginate_query` shape."""

    list: list[CustomerDailyConsumptionOut]
    total: int
    pageNo: int
    pageSize: int


# ---------------------------------------------------------------------------
# CustomerHourlyConsumption
# ---------------------------------------------------------------------------

class CustomerHourlyConsumptionBase(BaseModel):
    """Common fields for hourly consumption record."""

    customer_account_id: Optional[int] = None
    inquiry_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    data_date: Optional[date] = None
    data_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    hour_index: Optional[int] = Field(None, ge=0, le=23, description="小时索引 0-23")
    consumption: Optional[Decimal] = None
    time_period: Optional[int] = Field(None, description="时段: 1=尖峰, 2=高峰, 3=平时, 4=低谷")
    data_type: Optional[int] = Field(1)
    data_source: Optional[int] = Field(1)
    package_type: Optional[int] = None
    retail_unit_price: Optional[Decimal] = None
    delivered_unit_price: Optional[Decimal] = None
    wholesale_unit_price: Optional[Decimal] = None
    remarks: Optional[str] = None
    region: Optional[str] = Field(None, max_length=20)


class CustomerHourlyConsumptionCreate(CustomerHourlyConsumptionBase):
    """Create schema."""

    pass


class CustomerHourlyConsumptionUpdate(BaseModel):
    """Update schema."""

    id: int
    customer_account_id: Optional[int] = None
    inquiry_id: Optional[int] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    data_date: Optional[date] = None
    data_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    hour_index: Optional[int] = Field(None, ge=0, le=23)
    consumption: Optional[Decimal] = None
    time_period: Optional[int] = None
    data_type: Optional[int] = None
    data_source: Optional[int] = None
    package_type: Optional[int] = None
    retail_unit_price: Optional[Decimal] = None
    delivered_unit_price: Optional[Decimal] = None
    wholesale_unit_price: Optional[Decimal] = None
    remarks: Optional[str] = None
    region: Optional[str] = Field(None, max_length=20)


class CustomerHourlyConsumptionOut(CustomerHourlyConsumptionBase):
    """Output schema."""

    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class CustomerHourlyConsumptionPageOut(BaseModel):
    """Paginated output matching `paginate_query` shape."""

    list: list[CustomerHourlyConsumptionOut]
    total: int
    pageNo: int
    pageSize: int


# ---------------------------------------------------------------------------
# Point96Data
# ---------------------------------------------------------------------------

class Point96DataBase(BaseModel):
    """Common fields for 96-point curve data."""

    customer_account_id: Optional[int] = None
    market_member_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    measure_point: Optional[str] = Field(None, max_length=50)
    data_date: Optional[date] = None
    is_contracted: Optional[bool] = None
    trading_unit_name: Optional[str] = Field(None, max_length=100)
    total_consumption: Optional[Decimal] = None
    points: Optional[Point96Dict] = Field(
        default_factory=dict,
        description="96点电量 {HH:MM -> value}",
    )
    batch_no: Optional[str] = Field(None, max_length=50)
    processed: Optional[int] = Field(0)
    convert_time: Optional[date] = None
    region: Optional[str] = Field(None, max_length=20)

    @field_validator("points")
    @classmethod
    def check_points(cls, v: Point96Dict | None) -> Point96Dict | None:
        return _validate_point_keys(v)


class Point96DataCreate(Point96DataBase):
    """Create schema."""

    pass


class Point96DataUpdate(BaseModel):
    """Update schema."""

    id: int
    customer_account_id: Optional[int] = None
    market_member_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    measure_point: Optional[str] = Field(None, max_length=50)
    data_date: Optional[date] = None
    is_contracted: Optional[bool] = None
    trading_unit_name: Optional[str] = Field(None, max_length=100)
    total_consumption: Optional[Decimal] = None
    points: Optional[Point96Dict] = Field(None, description="96点电量 {HH:MM -> value}")
    batch_no: Optional[str] = Field(None, max_length=50)
    processed: Optional[int] = None
    convert_time: Optional[date] = None
    region: Optional[str] = Field(None, max_length=20)

    @field_validator("points")
    @classmethod
    def check_points(cls, v: Point96Dict | None) -> Point96Dict | None:
        return _validate_point_keys(v)


class Point96DataOut(Point96DataBase):
    """Output schema."""

    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class Point96DataPageOut(BaseModel):
    """Paginated output matching `paginate_query` shape."""

    list: list[Point96DataOut]
    total: int
    pageNo: int
    pageSize: int
