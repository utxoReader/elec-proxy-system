"""Commission settlement business logic.

Covers:
- CommissionConfig (分润配置)
- AgentFee (代理费/佣金)

State machine:
  AgentFee: pending_approval(1) → approved(2) → settled(3) → paid(4)
                                   → rejected(3)
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.commission import CommissionConfig
from app.models.agent import AgentFee, Agent
from app.models.profit import CustomerMonthlyProfit


# ========== Commission Config ==========


def list_commission_configs(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    effective_month: Optional[str] = None,
    status: Optional[int] = None,
) -> dict:
    q = db.query(CommissionConfig).filter(CommissionConfig.deleted_at.is_(None))
    if effective_month:
        q = q.filter(CommissionConfig.effective_month == effective_month)
    if status is not None:
        q = q.filter(CommissionConfig.status == status)
    total = q.count()
    items = (
        q.order_by(CommissionConfig.effective_month.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_commission_config(db: Session, id: int) -> Optional[CommissionConfig]:
    return (
        db.query(CommissionConfig)
        .filter(CommissionConfig.id == id, CommissionConfig.deleted_at.is_(None))
        .first()
    )


def get_current_effective_config(db: Session) -> Optional[CommissionConfig]:
    return (
        db.query(CommissionConfig)
        .filter(CommissionConfig.deleted_at.is_(None))
        .order_by(CommissionConfig.effective_month.desc())
        .first()
    )


def get_config_by_effective_month(db: Session, effective_month: str) -> Optional[CommissionConfig]:
    return (
        db.query(CommissionConfig)
        .filter(
            CommissionConfig.effective_month == effective_month,
            CommissionConfig.deleted_at.is_(None),
        )
        .first()
    )


def create_commission_config(db: Session, data) -> CommissionConfig:
    obj = CommissionConfig(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_commission_config(db: Session, data) -> Optional[CommissionConfig]:
    obj = get_commission_config(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_commission_config(db: Session, id: int) -> bool:
    obj = get_commission_config(db, id)
    if not obj:
        return False
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def validate_effective_month(db: Session, effective_month: str, exclude_id: Optional[int] = None) -> dict:
    """Validate that a month is available for config (cannot modify current or past months)."""
    from datetime import datetime

    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    if effective_month <= current_month:
        return {"valid": False, "message": "不能配置当月及历史月份的分润比例"}

    existing = get_config_by_effective_month(db, effective_month)
    if existing and (exclude_id is None or existing.id != exclude_id):
        return {"valid": False, "message": "该月份已存在分润配置"}

    return {"valid": True, "message": "ok"}


def preview_commission(db: Session, total_profit: Decimal) -> dict:
    """Preview commission distribution based on current config."""
    config = get_current_effective_config(db)
    agent_rate = (config.agent_commission_rate / Decimal("100")) if config and config.agent_commission_rate else Decimal("0.50")
    parent_rate = (config.parent_commission_rate / Decimal("100")) if config and config.parent_commission_rate else Decimal("0.05")

    agent_amount = (total_profit * agent_rate).quantize(Decimal("0.01"))
    parent_amount = (total_profit * parent_rate).quantize(Decimal("0.01"))
    company_amount = (total_profit - agent_amount - parent_amount).quantize(Decimal("0.01"))

    return {
        "total_profit": total_profit,
        "agent_rate": agent_rate,
        "agent_amount": agent_amount,
        "parent_rate": parent_rate,
        "parent_amount": parent_amount,
        "company_amount": company_amount,
    }


# ========== Agent Fee ==========


def list_agent_fees(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    agent_id: Optional[int] = None,
    fee_month: Optional[str] = None,
    approval_status: Optional[int] = None,
    settlement_status: Optional[int] = None,
) -> dict:
    q = db.query(AgentFee).filter(AgentFee.deleted_at.is_(None))
    if agent_id:
        q = q.filter(AgentFee.agent_id == agent_id)
    if fee_month:
        q = q.filter(AgentFee.fee_month == fee_month)
    if approval_status is not None:
        q = q.filter(AgentFee.approval_status == approval_status)
    if settlement_status is not None:
        q = q.filter(AgentFee.settlement_status == settlement_status)
    total = q.count()
    items = (
        q.order_by(AgentFee.fee_month.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_agent_fee(db: Session, id: int) -> Optional[AgentFee]:
    return (
        db.query(AgentFee)
        .filter(AgentFee.id == id, AgentFee.deleted_at.is_(None))
        .first()
    )


def create_agent_fee(db: Session, data) -> AgentFee:
    obj = AgentFee(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_agent_fee(db: Session, data) -> Optional[AgentFee]:
    obj = get_agent_fee(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_agent_fee(db: Session, id: int) -> bool:
    obj = get_agent_fee(db, id)
    if not obj:
        return False
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def batch_delete_agent_fees(db: Session, ids: list[int]) -> int:
    count = 0
    for fid in ids:
        if delete_agent_fee(db, fid):
            count += 1
    return count


def get_agent_fee_statistics(db: Session, agent_id: Optional[int] = None) -> dict:
    """Get commission statistics."""
    q = db.query(AgentFee).filter(AgentFee.deleted_at.is_(None))
    if agent_id:
        q = q.filter(AgentFee.agent_id == agent_id)

    rows = q.all()
    total = Decimal("0")
    pending = Decimal("0")
    approved = Decimal("0")
    settled = Decimal("0")
    paid = Decimal("0")

    for r in rows:
        amount = r.commission_amount or Decimal("0")
        total += amount
        if r.approval_status == 1:
            pending += amount
        elif r.approval_status == 2:
            approved += amount
        if r.settlement_status == 2:
            settled += amount
        elif r.settlement_status == 3:
            paid += amount

    return {
        "total_amount": total,
        "pending_approval_amount": pending,
        "approved_amount": approved,
        "settled_amount": settled,
        "paid_amount": paid,
        "count": len(rows),
    }


def generate_agent_fee_from_monthly_profit(
    db: Session, monthly_profit_id: int
) -> dict:
    """Generate agent fee record from a monthly profit record."""
    monthly = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.id == monthly_profit_id,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .first()
    )
    if not monthly:
        return {"success": False, "message": "月度利润记录不存在"}
    if not monthly.agent_id:
        return {"success": False, "message": "该利润记录无关联代理商"}

    # Check if fee already exists
    existing = (
        db.query(AgentFee)
        .filter(
            AgentFee.agent_id == monthly.agent_id,
            AgentFee.customer_account_id == monthly.customer_id,
            AgentFee.fee_month == monthly.profit_month,
            AgentFee.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "该代理商费用已生成"}

    agent = db.query(Agent).filter(Agent.id == monthly.agent_id).first()
    agent_name = agent.name if agent else f"代理商_{monthly.agent_id}"

    fee = AgentFee(
        agent_id=monthly.agent_id,
        agent_name=agent_name,
        customer_account_id=monthly.customer_id,
        customer_name=monthly.customer_name,
        fee_month=monthly.profit_month,
        config_month=monthly.profit_month,
        fee_date=date.today(),
        fee_type=1,  # commission
        customer_consumption=monthly.final_consumption,
        customer_payment=monthly.retail_fee,
        company_cost=(monthly.wholesale_fee or Decimal("0")) + (monthly.market_allocation_fee or Decimal("0")),
        gross_profit=monthly.adjusted_total_profit,
        commission_rate=monthly.agent_commission_rate,
        commission_amount=monthly.agent_commission_amount,
        tax_type=monthly.agent_tax_type,
        net_amount=monthly.agent_net_amount,
        remark="月度利润结算后自动生成",
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return {"success": True, "data": fee}


def approve_agent_fee(db: Session, id: int, approve_status: int, approve_remark: Optional[str] = None) -> dict:
    """Approve or reject an agent fee."""
    fee = get_agent_fee(db, id)
    if not fee:
        return {"success": False, "message": "记录不存在"}
    if fee.approval_status != 1:
        return {"success": False, "message": "当前状态不允许审批"}
    fee.approval_status = approve_status
    fee.approval_time = datetime.now(timezone.utc)
    fee.approval_comment = approve_remark
    db.commit()
    return {"success": True}


def batch_approve_agent_fees(
    db: Session, ids: list[int], approve_status: int, remark: Optional[str] = None
) -> dict:
    """Batch approve/reject agent fees."""
    count = 0
    for fid in ids:
        result = approve_agent_fee(db, fid, approve_status, remark)
        if result.get("success"):
            count += 1
    return {"success": True, "updated_count": count}


def settle_agent_fee(db: Session, id: int, remark: Optional[str] = None) -> dict:
    """Settle an agent fee (mark as settled)."""
    fee = get_agent_fee(db, id)
    if not fee:
        return {"success": False, "message": "记录不存在"}
    if fee.approval_status != 2:
        return {"success": False, "message": "请先审批通过再结算"}
    fee.settlement_status = 2  # settled
    fee.settlement_date = date.today()
    db.commit()
    return {"success": True}


def batch_settle_agent_fees(db: Session, ids: list[int], remark: Optional[str] = None) -> dict:
    """Batch settle agent fees."""
    count = 0
    for fid in ids:
        result = settle_agent_fee(db, fid, remark)
        if result.get("success"):
            count += 1
    return {"success": True, "updated_count": count}


def calculate_agent_fee_preview(db: Session, agent_id: int, fee_month: str) -> dict:
    """Pure calculation preview of agent fee without persisting."""
    monthly_profits = (
        db.query(CustomerMonthlyProfit)
        .filter(
            CustomerMonthlyProfit.agent_id == agent_id,
            CustomerMonthlyProfit.profit_month == fee_month,
            CustomerMonthlyProfit.deleted_at.is_(None),
        )
        .all()
    )

    total_customer_payment = sum((r.retail_fee or Decimal("0")) for r in monthly_profits)
    total_company_cost = sum(
        (r.wholesale_fee or Decimal("0")) + (r.market_allocation_fee or Decimal("0"))
        for r in monthly_profits
    )
    total_gross_profit = sum((r.adjusted_total_profit or r.total_profit or Decimal("0")) for r in monthly_profits)
    total_consumption = sum((r.final_consumption or r.total_consumption or Decimal("0")) for r in monthly_profits)
    total_commission = sum((r.agent_commission_amount or Decimal("0")) for r in monthly_profits)

    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    return {
        "agent_id": agent_id,
        "agent_name": agent.name if agent else None,
        "fee_month": fee_month,
        "customer_count": len(monthly_profits),
        "total_consumption": total_consumption,
        "total_customer_payment": total_customer_payment,
        "total_company_cost": total_company_cost,
        "total_gross_profit": total_gross_profit,
        "total_commission": total_commission,
        "monthly_profits": [
            {
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "total_profit": r.total_profit,
                "adjusted_profit": r.adjusted_total_profit,
                "commission_amount": r.agent_commission_amount,
            }
            for r in monthly_profits
        ],
    }


def export_agent_fee_excel(
    db: Session,
    agent_id: Optional[int] = None,
    fee_month: Optional[str] = None,
    approval_status: Optional[int] = None,
) -> dict:
    """Export agent fees as Excel file."""
    from openpyxl import Workbook
    from io import BytesIO

    fees = list_agent_fees(db, page=1, page_size=10000, agent_id=agent_id,
                            fee_month=fee_month, approval_status=approval_status)
    items = fees["items"]

    wb = Workbook()
    ws = wb.active
    ws.title = "代理费用"

    # Headers
    headers = ["ID", "代理商ID", "代理商名称", "月份", "客户名称", "用电量(kWh)",
               "客户支付额", "公司成本", "毛利润", "佣金比例", "佣金金额",
               "审批状态", "审批时间", "结算状态", "结算日期", "备注"]
    ws.append(headers)

    status_map = {1: "待审核", 2: "已审核", 3: "已驳回"}
    settle_status_map = {1: "待结算", 2: "已结算", 3: "已支付"}

    for fee in items:
        ws.append([
            fee.id, fee.agent_id, fee.agent_name, fee.fee_month, fee.customer_name,
            float(fee.customer_consumption or 0),
            float(fee.customer_payment or 0),
            float(fee.company_cost or 0),
            float(fee.gross_profit or 0),
            float(fee.commission_rate or 0),
            float(fee.commission_amount or 0),
            status_map.get(fee.approval_status or 1, str(fee.approval_status)),
            str(fee.approval_time or ""),
            settle_status_map.get(fee.settlement_status or 1, str(fee.settlement_status)),
            str(fee.settlement_date or ""),
            fee.remark or "",
        ])

    # Adjust column widths
    for col in ws.columns:
        max_length = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 30)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"代理费用_{fee_month or 'all'}.xlsx"
    return {"content": output.getvalue(), "filename": filename}
