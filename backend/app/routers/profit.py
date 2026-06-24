"""Profit calculation routers.

Three-tier profit hierarchy: hourly → daily → monthly.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.profit import (
    DailyProfitCalculateQuery,
    BatchDateRange,
    MonthlyProfitAdjustment,
    MonthlyProfitConfirm,
    MonthlyProfitSettlement,
    MonthlyProfitBatchGenerate,
    MonthlyProfitRecalculate,
    MonthlyProfitAgentFeesGenerate,
)
from app.services import profit as svc

router = APIRouter(prefix="/elec")


# ========== Hourly Profit ==========


@router.get("/customer-hourly-profit/daily-detail", response_model=ApiResponse)
def get_daily_hourly_detail(
    customer_id: int = Query(...),
    profit_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = svc.get_daily_hourly_detail(db, customer_id, profit_date)
    return ApiResponse(data=data)


@router.get("/customer-hourly-profit/monthly-detail", response_model=ApiResponse)
def get_monthly_hourly_detail(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_monthly_hourly_detail(db, customer_id, profit_month)
    return ApiResponse(data=data)


@router.get("/customer-hourly-profit/time-period-summary", response_model=ApiResponse)
def get_time_period_summary(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_time_period_summary(db, customer_id, profit_month)
    return ApiResponse(data=data)


@router.get("/customer-hourly-profit/monthly-hour-summary", response_model=ApiResponse)
def get_monthly_hour_summary(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_monthly_hourly_detail(db, customer_id, profit_month)
    return ApiResponse(data=data)


@router.get("/customer-hourly-profit/daily-summary", response_model=ApiResponse)
def get_daily_hourly_summary(
    customer_id: int = Query(...),
    profit_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = svc.get_daily_hourly_summary(db, customer_id, profit_date)
    return ApiResponse(data=data)


@router.get("/customer-hourly-profit/hourly-average", response_model=ApiResponse)
def get_hourly_average(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_hourly_average(db, customer_id, profit_month)
    return ApiResponse(data=data)


# ========== Daily Profit ==========


@router.get("/customer-daily-profit/page", response_model=ApiResponse)
def list_daily_profits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int = Query(None),
    agent_id: int = Query(None),
    profit_date: str = Query(None),
    profit_month: str = Query(None, description="YYYY-MM"),
    status: int = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.list_daily_profits(db, page, page_size, customer_id, agent_id, profit_date, profit_month, status)
    return ApiResponse(data=result)


@router.get("/customer-daily-profit/get/{id}", response_model=ApiResponse)
def get_daily_profit(id: int, db: Session = Depends(get_db)):
    obj = svc.get_daily_profit(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/customer-daily-profit/by-date", response_model=ApiResponse)
def get_daily_profit_by_date(
    customer_id: int = Query(...),
    profit_date: date = Query(...),
    db: Session = Depends(get_db),
):
    obj = svc.get_daily_profit_by_date(db, customer_id, profit_date)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/customer-daily-profit/monthly-summary", response_model=ApiResponse)
def get_daily_profit_monthly_summary(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_daily_profit_monthly_summary(db, customer_id, profit_month)
    return ApiResponse(data=data)


@router.post("/customer-daily-profit/batch-calculate-from-daily-data", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def batch_calculate_daily_profit(
    payload: BatchDateRange,
    db: Session = Depends(get_db),
):
    result = svc.batch_calculate_daily_profit(
        db, payload.start_date, payload.end_date
    )
    return ApiResponse(data=result)


@router.post("/customer-daily-profit/calculate-from-daily-data", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def calculate_daily_profit(payload: DailyProfitCalculateQuery, db: Session = Depends(get_db)):
    result = svc.calculate_daily_profit(db, payload.customer_account_id, payload.date)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "计算失败"))
    return ApiResponse(message="Calculated", data=result.get("data"))


# ========== Monthly Profit ==========


@router.get("/customer-monthly-profit/by-month", response_model=ApiResponse)
def get_monthly_profits_by_month(
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_monthly_profits_by_month(db, profit_month)
    return ApiResponse(data=data)


@router.post("/customer-monthly-profit/batch-generate-from-daily-data", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def batch_generate_monthly_profit(
    payload: MonthlyProfitBatchGenerate,
    db: Session = Depends(get_db),
):
    result = svc.batch_generate_monthly_profit(db, payload.profit_month)
    return ApiResponse(data=result)


@router.post("/customer-monthly-profit/recalculate/{id}", response_model=ApiResponse)
def recalculate_adjusted_profit(id: int, db: Session = Depends(get_db)):
    result = svc.recalculate_adjusted_profit(db, id)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "重算失败"))
    return ApiResponse(message="Recalculated", data=result.get("data"))


@router.post("/customer-monthly-profit/batch-recalculate", response_model=ApiResponse)
def batch_recalculate_adjusted_profit(
    payload: MonthlyProfitRecalculate,
    db: Session = Depends(get_db),
):
    result = svc.batch_recalculate_adjusted_profit(db, payload.ids)
    return ApiResponse(data=result)


@router.get("/customer-monthly-profit/agent-summary", response_model=ApiResponse)
def get_agent_monthly_summary(
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.get_agent_monthly_summary(db, profit_month)
    return ApiResponse(data=data)


@router.get("/customer-monthly-profit/completeness-check", response_model=ApiResponse)
def check_monthly_data_completeness(
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    data = svc.check_monthly_data_completeness(db, profit_month)
    return ApiResponse(data=data)


@router.get("/customer-monthly-profit/ranking", response_model=ApiResponse)
def get_monthly_profit_ranking(
    profit_month: str = Query(..., description="YYYY-MM"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    data = svc.get_monthly_profit_ranking(db, profit_month, limit)
    return ApiResponse(data=data)


@router.get("/customer-monthly-profit/agent-performance", response_model=ApiResponse)
def get_agent_monthly_performance(
    profit_month: str = Query(..., description="YYYY-MM"),
    agent_id: int = Query(...),
    db: Session = Depends(get_db),
):
    data = svc.get_agent_monthly_performance(db, profit_month, agent_id)
    return ApiResponse(data=data)


@router.post("/customer-monthly-profit/generate-agent-fees", response_model=ApiResponse)
def generate_agent_fees_from_monthly_profit(
    payload: MonthlyProfitAgentFeesGenerate,
    db: Session = Depends(get_db),
):
    result = svc.generate_agent_fees_from_monthly_profits(
        db, payload.profit_month, payload.agent_ids
    )
    return ApiResponse(data=result)


@router.get("/customer-monthly-profit/page", response_model=ApiResponse)
def list_monthly_profits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int = Query(None),
    agent_id: int = Query(None),
    profit_month: str = Query(None, description="YYYY-MM"),
    status: int = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.list_monthly_profits(db, page, page_size, customer_id, agent_id, profit_month, status)
    return ApiResponse(data=result)


@router.get("/customer-monthly-profit/get/{id}", response_model=ApiResponse)
def get_monthly_profit(id: int, db: Session = Depends(get_db)):
    obj = svc.get_monthly_profit(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/customer-monthly-profit/by-customer-and-month", response_model=ApiResponse)
def get_monthly_profit_by_customer(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    obj = svc.get_monthly_profit(db, customer_id)
    return ApiResponse(data=obj)


@router.post("/customer-monthly-profit/generate-from-daily-data", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def generate_monthly_profit(
    customer_id: int = Query(...),
    profit_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    result = svc.generate_monthly_profit(db, customer_id, profit_month)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "生成失败"))
    return ApiResponse(message="Generated", data=result.get("data"))


@router.post("/customer-monthly-profit/adjust", response_model=ApiResponse)
def adjust_monthly_profit(payload: MonthlyProfitAdjustment, db: Session = Depends(get_db)):
    result = svc.adjust_monthly_profit(db, payload.id, payload.adjustment_consumption, payload.adjustment_remark)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "调平失败"))
    return ApiResponse(message="Adjusted", data=result.get("data"))


@router.post("/customer-monthly-profit/confirm", response_model=ApiResponse)
def confirm_monthly_profit(payload: MonthlyProfitConfirm, db: Session = Depends(get_db)):
    result = svc.confirm_monthly_profit(db, payload.ids, payload.confirm_remark)
    return ApiResponse(data=result)


@router.post("/customer-monthly-profit/settle", response_model=ApiResponse)
def settle_monthly_profit(payload: MonthlyProfitSettlement, db: Session = Depends(get_db)):
    result = svc.settle_monthly_profit(db, payload.id, payload.settlement_remark)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "结算失败"))
    return ApiResponse(message="Settled")


@router.get("/customer-monthly-profit/summary", response_model=ApiResponse)
def get_monthly_profit_summary(
    profit_month: str = Query(..., description="YYYY-MM"),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
):
    data = svc.get_monthly_profit_summary(db, profit_month, agent_id)
    return ApiResponse(data=data)


@router.get("/customer-monthly-profit/export-excel")
def export_monthly_profit_excel(
    profit_month: str = Query(..., description="YYYY-MM"),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
):
    return svc.export_monthly_profit_excel(db, profit_month, agent_id)
