"""Pydantic schemas for usage curve template."""

from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class UsageCurveTemplateBase(BaseModel):
    """Common fields for usage curve template."""

    template_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    template_type: Optional[int] = None
    industry: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=200)
    hour_00_ratio: Optional[Decimal] = None
    hour_01_ratio: Optional[Decimal] = None
    hour_02_ratio: Optional[Decimal] = None
    hour_03_ratio: Optional[Decimal] = None
    hour_04_ratio: Optional[Decimal] = None
    hour_05_ratio: Optional[Decimal] = None
    hour_06_ratio: Optional[Decimal] = None
    hour_07_ratio: Optional[Decimal] = None
    hour_08_ratio: Optional[Decimal] = None
    hour_09_ratio: Optional[Decimal] = None
    hour_10_ratio: Optional[Decimal] = None
    hour_11_ratio: Optional[Decimal] = None
    hour_12_ratio: Optional[Decimal] = None
    hour_13_ratio: Optional[Decimal] = None
    hour_14_ratio: Optional[Decimal] = None
    hour_15_ratio: Optional[Decimal] = None
    hour_16_ratio: Optional[Decimal] = None
    hour_17_ratio: Optional[Decimal] = None
    hour_18_ratio: Optional[Decimal] = None
    hour_19_ratio: Optional[Decimal] = None
    hour_20_ratio: Optional[Decimal] = None
    hour_21_ratio: Optional[Decimal] = None
    hour_22_ratio: Optional[Decimal] = None
    hour_23_ratio: Optional[Decimal] = None
    hour_00_peak_ratio: Optional[Decimal] = None
    hour_01_peak_ratio: Optional[Decimal] = None
    hour_02_peak_ratio: Optional[Decimal] = None
    hour_03_peak_ratio: Optional[Decimal] = None
    hour_04_peak_ratio: Optional[Decimal] = None
    hour_05_peak_ratio: Optional[Decimal] = None
    hour_06_peak_ratio: Optional[Decimal] = None
    hour_07_peak_ratio: Optional[Decimal] = None
    hour_08_peak_ratio: Optional[Decimal] = None
    hour_09_peak_ratio: Optional[Decimal] = None
    hour_10_peak_ratio: Optional[Decimal] = None
    hour_11_peak_ratio: Optional[Decimal] = None
    hour_12_peak_ratio: Optional[Decimal] = None
    hour_13_peak_ratio: Optional[Decimal] = None
    hour_14_peak_ratio: Optional[Decimal] = None
    hour_15_peak_ratio: Optional[Decimal] = None
    hour_16_peak_ratio: Optional[Decimal] = None
    hour_17_peak_ratio: Optional[Decimal] = None
    hour_18_peak_ratio: Optional[Decimal] = None
    hour_19_peak_ratio: Optional[Decimal] = None
    hour_20_peak_ratio: Optional[Decimal] = None
    hour_21_peak_ratio: Optional[Decimal] = None
    hour_22_peak_ratio: Optional[Decimal] = None
    hour_23_peak_ratio: Optional[Decimal] = None
    status: Optional[int] = Field(1)
    is_default: Optional[int] = Field(0)
    sort: Optional[int] = None
    region: Optional[str] = Field(None, max_length=20)


class UsageCurveTemplateCreate(UsageCurveTemplateBase):
    """Create schema."""

    pass


class UsageCurveTemplateUpdate(BaseModel):
    """Update schema."""

    id: int
    template_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    template_type: Optional[int] = None
    industry: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=200)
    hour_00_ratio: Optional[Decimal] = None
    hour_01_ratio: Optional[Decimal] = None
    hour_02_ratio: Optional[Decimal] = None
    hour_03_ratio: Optional[Decimal] = None
    hour_04_ratio: Optional[Decimal] = None
    hour_05_ratio: Optional[Decimal] = None
    hour_06_ratio: Optional[Decimal] = None
    hour_07_ratio: Optional[Decimal] = None
    hour_08_ratio: Optional[Decimal] = None
    hour_09_ratio: Optional[Decimal] = None
    hour_10_ratio: Optional[Decimal] = None
    hour_11_ratio: Optional[Decimal] = None
    hour_12_ratio: Optional[Decimal] = None
    hour_13_ratio: Optional[Decimal] = None
    hour_14_ratio: Optional[Decimal] = None
    hour_15_ratio: Optional[Decimal] = None
    hour_16_ratio: Optional[Decimal] = None
    hour_17_ratio: Optional[Decimal] = None
    hour_18_ratio: Optional[Decimal] = None
    hour_19_ratio: Optional[Decimal] = None
    hour_20_ratio: Optional[Decimal] = None
    hour_21_ratio: Optional[Decimal] = None
    hour_22_ratio: Optional[Decimal] = None
    hour_23_ratio: Optional[Decimal] = None
    hour_00_peak_ratio: Optional[Decimal] = None
    hour_01_peak_ratio: Optional[Decimal] = None
    hour_02_peak_ratio: Optional[Decimal] = None
    hour_03_peak_ratio: Optional[Decimal] = None
    hour_04_peak_ratio: Optional[Decimal] = None
    hour_05_peak_ratio: Optional[Decimal] = None
    hour_06_peak_ratio: Optional[Decimal] = None
    hour_07_peak_ratio: Optional[Decimal] = None
    hour_08_peak_ratio: Optional[Decimal] = None
    hour_09_peak_ratio: Optional[Decimal] = None
    hour_10_peak_ratio: Optional[Decimal] = None
    hour_11_peak_ratio: Optional[Decimal] = None
    hour_12_peak_ratio: Optional[Decimal] = None
    hour_13_peak_ratio: Optional[Decimal] = None
    hour_14_peak_ratio: Optional[Decimal] = None
    hour_15_peak_ratio: Optional[Decimal] = None
    hour_16_peak_ratio: Optional[Decimal] = None
    hour_17_peak_ratio: Optional[Decimal] = None
    hour_18_peak_ratio: Optional[Decimal] = None
    hour_19_peak_ratio: Optional[Decimal] = None
    hour_20_peak_ratio: Optional[Decimal] = None
    hour_21_peak_ratio: Optional[Decimal] = None
    hour_22_peak_ratio: Optional[Decimal] = None
    hour_23_peak_ratio: Optional[Decimal] = None
    status: Optional[int] = None
    is_default: Optional[int] = None
    sort: Optional[int] = None
    region: Optional[str] = Field(None, max_length=20)


class UsageCurveTemplateOut(UsageCurveTemplateBase):
    """Output schema."""

    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class UsageCurveTemplatePageOut(BaseModel):
    """Paginated output matching `paginate_query` shape."""

    list: list[UsageCurveTemplateOut]
    total: int
    pageNo: int
    pageSize: int
