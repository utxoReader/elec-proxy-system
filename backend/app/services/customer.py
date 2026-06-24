"""Customer management business logic."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.models.customer_account import CustomerAccount, CustomerAccountPriceHistory
from app.schemas.customer import (
    CustomerAccountCreate, CustomerAccountUpdate,
    CustomerPriceChange, CustomerStatusChange,
)


def _model_to_dict(model_obj: Any, exclude_fields: set = None) -> dict:
    """Convert a SQLAlchemy model instance to a dict for JSON serialization."""
    if model_obj is None:
        return None
    exclude = exclude_fields or set()
    exclude.add("_sa_instance_state")
    mapper = inspect(model_obj)
    result = {}
    for attr in mapper.attrs:
        key = attr.key
        if key in exclude:
            continue
        value = getattr(model_obj, key, None)
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        result[key] = value
    return result


def _models_to_dicts(models: list, exclude_fields: set = None) -> list[dict]:
    """Convert a list of SQLAlchemy models to dicts."""
    return [_model_to_dict(m, exclude_fields) for m in models]


def list_customers_no_page(db: Session, customer_name: Optional[str] = None,
                            customer_status: Optional[int] = None,
                            agent_id: Optional[int] = None) -> list:
    """获取客户列表（无分页）"""
    q = db.query(CustomerAccount).filter(CustomerAccount.deleted_at.is_(None))
    if customer_name:
        q = q.filter(CustomerAccount.customer_name.ilike(f"%{customer_name}%"))
    if customer_status is not None:
        q = q.filter(CustomerAccount.customer_status == customer_status)
    if agent_id is not None:
        q = q.filter(CustomerAccount.agent_id == agent_id)
    return _models_to_dicts(q.order_by(CustomerAccount.created_at.desc()).all())


def get_customers_by_agent(db: Session, agent_id: int) -> list:
    """根据代理商ID获取客户列表"""
    return _models_to_dicts(
        db.query(CustomerAccount).filter(
            CustomerAccount.deleted_at.is_(None),
            CustomerAccount.agent_id == agent_id,
        ).order_by(CustomerAccount.customer_name).all()
    )


def get_customers_by_status(db: Session, customer_status: int) -> list:
    """根据状态获取客户列表"""
    return _models_to_dicts(
        db.query(CustomerAccount).filter(
            CustomerAccount.deleted_at.is_(None),
            CustomerAccount.customer_status == customer_status,
        ).order_by(CustomerAccount.customer_name).all()
    )


def get_customer_options(db: Session) -> list:
    """获取客户选项列表"""
    return _models_to_dicts(
        db.query(CustomerAccount).filter(
            CustomerAccount.deleted_at.is_(None),
        ).order_by(CustomerAccount.customer_name).all()
    )


def sign_contract(db: Session, id: int, data: CustomerAccountUpdate) -> Optional[dict]:
    """签约客户（需前置状态为待签约2，改为已签约3）
    匹配 Java 原版：要求 customer_status == 2（待签约）
    """
    obj = get_customer_raw(db, id)
    if not obj:
        return None
    if obj.customer_status != 2:
        return {"id": id, "error": "客户状态不是待签约，无法签约"}
    obj.customer_status = 3  # contracted
    for k, v in data.model_dump(exclude={"id", "customer_status"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj)


def terminate_contract(db: Session, id: int, reason: str, terminate_date: str) -> Optional[dict]:
    """终止客户合同
    匹配 Java 原版：保留 status=3，设置 contract_end_date 为终止日期，添加备注
    """
    obj = get_customer_raw(db, id)
    if not obj:
        return None
    if obj.customer_status != 3:
        return {"id": id, "error": "客户不是已签约状态，无法终止合同"}
    # Java 原版：保留 status=3，改 end_date，加备注
    from datetime import date as d
    obj.contract_end_date = d.fromisoformat(terminate_date)
    obj.remark = (obj.remark or "") + f" [合同终止: {reason} 于 {terminate_date}]"
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj)


def delete_customer(db: Session, id: int) -> bool:
    """删除客户（Java 原版禁止删除已签约客户 status==3）"""
    obj = get_customer_raw(db, id)
    if not obj:
        return False
    if obj.customer_status == 3:
        raise ValueError("不能删除已签约客户，请先终止合同")
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def batch_update_customer_status(db: Session, ids: list[int], customer_status: int) -> int:
    """批量更新客户状态"""
    count = db.query(CustomerAccount).filter(
        CustomerAccount.id.in_(ids),
        CustomerAccount.deleted_at.is_(None),
    ).update({"customer_status": customer_status}, synchronize_session=False)
    db.commit()
    return count


def count_customers_by_status(db: Session, customer_status: int) -> int:
    """统计某状态的客户数量"""
    return db.query(CustomerAccount).filter(
        CustomerAccount.deleted_at.is_(None),
        CustomerAccount.customer_status == customer_status,
    ).count()


def list_customers(db: Session, page: int = 1, page_size: int = 20,
                   customer_name: Optional[str] = None,
                   customer_status: Optional[int] = None,
                   agent_id: Optional[int] = None) -> dict:
    q = db.query(CustomerAccount).filter(CustomerAccount.deleted_at.is_(None))
    if customer_name:
        q = q.filter(CustomerAccount.customer_name.ilike(f"%{customer_name}%"))
    if customer_status is not None:
        q = q.filter(CustomerAccount.customer_status == customer_status)
    if agent_id is not None:
        q = q.filter(CustomerAccount.agent_id == agent_id)
    total = q.count()
    items = q.order_by(CustomerAccount.created_at.desc()) \
             .offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": _models_to_dicts(items)}


def list_simple_customers(db: Session) -> list:
    """Simplified list for dropdown selectors."""
    return db.query(
        CustomerAccount.id,
        CustomerAccount.customer_name,
        CustomerAccount.agent_id,
        CustomerAccount.customer_status,
    ).filter(CustomerAccount.deleted_at.is_(None)).order_by(CustomerAccount.customer_name).all()


def list_contracted_customers(db: Session) -> list:
    """List only contracted customers."""
    return _models_to_dicts(db.query(CustomerAccount).filter(
        CustomerAccount.deleted_at.is_(None),
        CustomerAccount.customer_status == 3,
    ).order_by(CustomerAccount.customer_name).all())


def get_customer(db: Session, id: int) -> Optional[dict]:
    obj = db.query(CustomerAccount).filter(
        CustomerAccount.id == id, CustomerAccount.deleted_at.is_(None)
    ).first()
    return _model_to_dict(obj)


def create_customer(db: Session, data: CustomerAccountCreate) -> dict:
    obj = CustomerAccount(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj)


def update_customer(db: Session, data: CustomerAccountUpdate) -> Optional[dict]:
    obj = get_customer_raw(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj)


def get_customer_raw(db: Session, id: int) -> Optional[CustomerAccount]:
    return db.query(CustomerAccount).filter(
        CustomerAccount.id == id, CustomerAccount.deleted_at.is_(None)
    ).first()


def update_customer_status(db: Session, data: CustomerStatusChange) -> Optional[dict]:
    obj = get_customer_raw(db, data.id)
    if not obj:
        return None
    obj.customer_status = data.customer_status
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj)


def change_customer_price(db: Session, data: CustomerPriceChange) -> Optional[dict]:
    """Change customer's price difference with history tracking.

    Matches Java original: creates a price history record with status=1 (待生效).
    Does NOT immediately update price_difference on the customer account.
    Requires customer status == 3 (已签约).
    A scheduled job reads pending records and applies them when effective_date arrives.
    """
    customer = get_customer_raw(db, data.customer_account_id)
    if not customer:
        return None

    # Java: only contracted customers can change price
    if customer.customer_status != 3:
        return {"id": customer.id, "error": "客户不是已签约状态，无法修改价差"}

    # Check for no-change request
    if (customer.price_difference == data.new_price_difference and
        str(customer.contract_start_date or "") == str(data.new_contract_start_date or "") and
        str(customer.contract_end_date or "") == str(data.new_contract_end_date or "")):
        return {"id": customer.id, "message": "No changes detected"}

    # Java original: only create a status=1 (pending) history record
    # Customer price_difference stays unchanged until scheduled job applies it
    history = CustomerAccountPriceHistory(
        customer_account_id=data.customer_account_id,
        customer_name=customer.customer_name,
        old_price_difference=customer.price_difference,
        new_price_difference=data.new_price_difference,
        old_contract_start_date=customer.contract_start_date,
        old_contract_end_date=customer.contract_end_date,
        new_contract_start_date=data.new_contract_start_date or customer.contract_start_date,
        new_contract_end_date=data.new_contract_end_date or customer.contract_end_date,
        effective_date=data.effective_date,
        change_reason=data.change_reason,
        change_type=1 if not (data.new_contract_start_date or data.new_contract_end_date) else 3,
        status=1,  # pending — not yet applied
    )
    db.add(history)

    db.commit()
    db.refresh(history)
    return _model_to_dict(customer)


# ============ Price History ============

def export_customers_excel(
    db: Session,
    customer_status: Optional[int] = None,
    agent_id: Optional[int] = None,
) -> StreamingResponse:
    """Export customer accounts as Excel."""
    from app.services.excel_utils import export_to_response

    q = db.query(CustomerAccount).filter(CustomerAccount.deleted_at.is_(None))
    if customer_status is not None:
        q = q.filter(CustomerAccount.customer_status == customer_status)
    if agent_id:
        q = q.filter(CustomerAccount.agent_id == agent_id)
    rows = q.order_by(CustomerAccount.customer_name).all()

    status_map = {1: "潜在客户", 2: "洽谈中", 3: "已签约", 4: "已终止"}
    headers = [
        "ID", "客户名称", "联系人", "联系电话", "代理商",
        "客户状态", "签约日期", "合同到期日", "用电地址",
        "电压等级", "行业分类", "创建时间",
    ]
    data = []
    for r in rows:
        data.append([
            r.id, r.customer_name or "", r.contact_person or "", r.contact_phone or "",
            r.agent_name or "",
            status_map.get(r.customer_status or 0, str(r.customer_status or "")),
            str(r.contract_start_date or ""),
            str(r.contract_end_date or ""),
            r.electricity_address or "", r.voltage_level or "",
            r.industry_category or "", str(r.created_at or ""),
        ])
    filename = "客户账户列表.xlsx"
    return export_to_response(headers, data, filename, "客户账户", left_align_cols={2, 8})


def download_customer_import_template() -> StreamingResponse:
    """Download blank customer import template."""
    from app.services.excel_utils import export_to_response
    headers = ["客户名称(*)", "联系人", "联系电话", "代理商ID", "用电地址", "电压等级", "行业分类", "备注"]
    data = [["示例客户", "张三", "13800138000", "1", "XX路100号", "10kV", "制造业", ""]]
    return export_to_response(headers, data, "客户账户导入模板.xlsx", "导入模板")


def import_customers_from_excel(db: Session, file) -> dict:
    """Import customer accounts from Excel."""
    from io import BytesIO
    import openpyxl

    if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传.xlsx格式文件")

    content = file.file.read()
    wb = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
    ws = wb.active

    created = 0
    errors = []
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        if row_idx == 1:
            continue
        if not row or not row[0]:
            continue
        try:
            customer = CustomerAccount(
                customer_name=str(row[0]),
                contact_person=str(row[1]) if row[1] else None,
                contact_phone=str(row[2]) if row[2] else None,
                agent_id=int(row[3]) if row[3] else None,
                electricity_address=str(row[4]) if row[4] else None,
                voltage_level=str(row[5]) if row[5] else None,
                industry_category=str(row[6]) if row[6] else None,
                remark=str(row[7]) if row[7] else None,
                customer_status=3,
            )
            db.add(customer)
            created += 1
        except Exception as e:
            errors.append({"row": row_idx, "error": str(e)})
    if created > 0:
        db.commit()
    return {"created": created, "errors": errors, "total": len(errors) + created}


def list_price_history(db: Session, page=1, page_size=20,
                       customer_account_id: Optional[int] = None) -> dict:
    q = db.query(CustomerAccountPriceHistory).filter(
        CustomerAccountPriceHistory.deleted_at.is_(None))
    if customer_account_id is not None:
        q = q.filter(CustomerAccountPriceHistory.customer_account_id == customer_account_id)
    total = q.count()
    items = q.order_by(CustomerAccountPriceHistory.created_at.desc()) \
             .offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": _models_to_dicts(items)}
