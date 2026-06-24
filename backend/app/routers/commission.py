"""Commission settlement routers.

Covers:
- CommissionConfig (分润配置)
- AgentFee (代理费/佣金)
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.commission import (
    CommissionConfigCreate,
    CommissionConfigUpdate,
    AgentFeeCreate,
    AgentFeeUpdate,
    AgentFeeCalculate,
    AgentFeeCalculatePreview,
    AgentFeeApproval,
    AgentFeeBatchApproval,
    AgentFeeBatchSettlement,
)
from app.services import commission as svc

router = APIRouter(prefix="/elec")


# ==================== CommissionConfig ====================


@router.get("/commission-config/page", response_model=ApiResponse)
def list_commission_configs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    effective_month: str = Query(None, description="YYYY-MM"),
    status: int = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.list_commission_configs(db, page, page_size, effective_month, status)
    return ApiResponse(data=result)


@router.get("/commission-config/get/{id}", response_model=ApiResponse)
def get_commission_config(id: int, db: Session = Depends(get_db)):
    obj = svc.get_commission_config(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/commission-config/current", response_model=ApiResponse)
def get_current_effective_config(db: Session = Depends(get_db)):
    obj = svc.get_current_effective_config(db)
    if not obj:
        return ApiResponse(success=False, message="No config found")
    return ApiResponse(data=obj)


@router.get("/commission-config/by-effective-month", response_model=ApiResponse)
def get_config_by_effective_month(
    effective_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    obj = svc.get_config_by_effective_month(db, effective_month)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/commission-config/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_commission_config(payload: CommissionConfigCreate, db: Session = Depends(get_db)):
    validation = svc.validate_effective_month(db, payload.effective_month)
    if not validation["valid"]:
        return ApiResponse(success=False, message=validation["message"])
    # Auto-calculate company rate if not provided
    if payload.company_commission_rate is None:
        total_rates = (payload.agent_commission_rate or Decimal("0")) + (payload.parent_commission_rate or Decimal("0"))
        payload.company_commission_rate = Decimal("100") - total_rates
    obj = svc.create_commission_config(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/commission-config/update", response_model=ApiResponse)
def update_commission_config(payload: CommissionConfigUpdate, db: Session = Depends(get_db)):
    obj = svc.update_commission_config(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/commission-config/delete/{id}", response_model=ApiResponse)
def delete_commission_config(id: int, db: Session = Depends(get_db)):
    ok = svc.delete_commission_config(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.post("/commission-config/validate-effective-month", response_model=ApiResponse)
def validate_effective_month(
    effective_month: str = Query(..., description="YYYY-MM"),
    exclude_id: int = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.validate_effective_month(db, effective_month, exclude_id)
    return ApiResponse(data=result)


@router.get("/commission-config/preview-commission", response_model=ApiResponse)
def preview_commission(
    total_profit: Decimal = Query(..., description="总利润金额"),
    db: Session = Depends(get_db),
):
    data = svc.preview_commission(db, total_profit)
    return ApiResponse(data=data)


# ==================== AgentFee ====================


@router.get("/agent-fee/page", response_model=ApiResponse)
def list_agent_fees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_id: int = Query(None),
    fee_month: str = Query(None, description="YYYY-MM"),
    approval_status: int = Query(None),
    settlement_status: int = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.list_agent_fees(db, page, page_size, agent_id, fee_month, approval_status, settlement_status)
    return ApiResponse(data=result)


@router.get("/agent-fee/get/{id}", response_model=ApiResponse)
def get_agent_fee(id: int, db: Session = Depends(get_db)):
    obj = svc.get_agent_fee(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/agent-fee/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_agent_fee(payload: AgentFeeCreate, db: Session = Depends(get_db)):
    obj = svc.create_agent_fee(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/agent-fee/update", response_model=ApiResponse)
def update_agent_fee(payload: AgentFeeUpdate, db: Session = Depends(get_db)):
    obj = svc.update_agent_fee(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/agent-fee/delete/{id}", response_model=ApiResponse)
def delete_agent_fee(id: int, db: Session = Depends(get_db)):
    ok = svc.delete_agent_fee(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.delete("/agent-fee/batch-delete", response_model=ApiResponse)
def batch_delete_agent_fees(ids: list[int] = Query(...), db: Session = Depends(get_db)):
    count = svc.batch_delete_agent_fees(db, ids)
    return ApiResponse(message=f"Deleted {count} records")


@router.get("/agent-fee/statistics", response_model=ApiResponse)
def get_agent_fee_statistics(
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
):
    data = svc.get_agent_fee_statistics(db, agent_id)
    return ApiResponse(data=data)


@router.post("/agent-fee/calculate-and-generate", response_model=ApiResponse)
def calculate_and_generate_agent_fee(payload: AgentFeeCalculate, db: Session = Depends(get_db)):
    result = svc.generate_agent_fee_from_monthly_profit(db, int(payload.agent_id))
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "生成失败"))
    return ApiResponse(message="Generated", data=result.get("data"))


@router.post("/agent-fee/approve", response_model=ApiResponse)
def approve_agent_fee(payload: AgentFeeApproval, db: Session = Depends(get_db)):
    result = svc.approve_agent_fee(db, payload.id, payload.approve_status, payload.approve_remark)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "审批失败"))
    return ApiResponse(message="Approved")


@router.post("/agent-fee/batch-approve", response_model=ApiResponse)
def batch_approve_agent_fees(payload: AgentFeeBatchApproval, db: Session = Depends(get_db)):
    result = svc.batch_approve_agent_fees(db, payload.ids, payload.approve_status, payload.approve_remark)
    return ApiResponse(data=result)


@router.post("/agent-fee/settle", response_model=ApiResponse)
def settle_agent_fee(
    id: int = Query(...),
    remark: str = Query(None),
    db: Session = Depends(get_db),
):
    result = svc.settle_agent_fee(db, id, remark)
    if not result.get("success"):
        return ApiResponse(success=False, message=result.get("message", "结算失败"))
    return ApiResponse(message="Settled")


@router.post("/agent-fee/batch-settle", response_model=ApiResponse)
def batch_settle_agent_fees(payload: AgentFeeBatchSettlement, db: Session = Depends(get_db)):
    result = svc.batch_settle_agent_fees(db, payload.ids, payload.settlement_remark)
    return ApiResponse(data=result)


@router.post("/agent-fee/calculate", response_model=ApiResponse)
def calculate_agent_fee_preview(
    payload: AgentFeeCalculatePreview,
    db: Session = Depends(get_db),
):
    """Pure calculation preview without persistence."""
    result = svc.calculate_agent_fee_preview(db, payload.agent_id, payload.fee_month)
    return ApiResponse(data=result)


@router.get("/agent-fee/export-excel")
def export_agent_fee_excel(
    agent_id: int = Query(None),
    fee_month: str = Query(None, description="YYYY-MM"),
    approval_status: int = Query(None),
    db: Session = Depends(get_db),
):
    """Export agent fees as Excel file."""
    result = svc.export_agent_fee_excel(db, agent_id, fee_month, approval_status)
    return StreamingResponse(
        iter([result["content"]]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
    )
