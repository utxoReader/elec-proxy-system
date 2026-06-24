"""Manual trigger endpoints for scheduled background jobs."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.services import scheduled_jobs as svc

router = APIRouter(prefix="/elec")


class DailyProfitRunRequest(BaseModel):
    target_date: date | None = Field(None, description="目标日期，默认昨天")


class MonthlyProfitRunRequest(BaseModel):
    target_month: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="目标月份 YYYY-MM，默认上月",
    )


class MonthlyCommissionRunRequest(BaseModel):
    target_month: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="目标月份 YYYY-MM，默认上月",
    )


class PriceEffectiveRunRequest(BaseModel):
    target_date: date | None = Field(None, description="目标日期，默认今天")


class ContractExpiryRunRequest(BaseModel):
    days_before: int = Field(7, ge=0, description="提前天数，默认 7 天")


@router.post("/jobs/daily-profit/run", response_model=ApiResponse)
def run_daily_profit(payload: DailyProfitRunRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """手动触发日利润计算任务。"""
    result = svc.run_daily_profit_calculation(db, payload.target_date)
    return ApiResponse(data=result)


@router.post("/jobs/monthly-profit/run", response_model=ApiResponse)
def run_monthly_profit(
    payload: MonthlyProfitRunRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    """手动触发月度利润聚合任务。"""
    result = svc.run_monthly_profit_aggregation(db, payload.target_month)
    return ApiResponse(data=result)


@router.post("/jobs/monthly-commission/run", response_model=ApiResponse)
def run_monthly_commission(
    payload: MonthlyCommissionRunRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    """手动触发月度佣金结算任务。"""
    result = svc.run_monthly_commission_settlement(db, payload.target_month)
    return ApiResponse(data=result)


@router.post("/jobs/price-effective/run", response_model=ApiResponse)
def run_price_effective(
    payload: PriceEffectiveRunRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    """手动触发价差生效任务。"""
    result = svc.run_price_effective_job(db, payload.target_date)
    return ApiResponse(data=result)


@router.post("/jobs/contract-expiry/run", response_model=ApiResponse)
def run_contract_expiry(
    payload: ContractExpiryRunRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    """手动触发合同到期提醒任务。"""
    result = svc.run_contract_expiry_reminder(db, payload.days_before)
    return ApiResponse(data=result)
