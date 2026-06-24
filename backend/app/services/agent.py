"""Agent management business logic."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentFee
from app.models.commission import CommissionConfig
from app.schemas.agent import (
    AgentCreate, AgentUpdate,
    CommissionConfigCreate, CommissionConfigUpdate,
)


# ============ Serialization helper ============

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


# ============ Agent ============

def get_agents_by_parent(db: Session, parent_id: int) -> list:
    """根据父级代理商ID获取子级代理商列表"""
    return _models_to_dicts(
        db.query(Agent).filter(
            Agent.parent_id == parent_id,
            Agent.deleted_at.is_(None),
        ).order_by(Agent.name).all(),
        {"password_hash"},
    )


def get_agents_by_type(db: Session, type: int) -> list:
    """根据代理商类型获取代理商列表"""
    return _models_to_dicts(
        db.query(Agent).filter(
            Agent.type == type,
            Agent.deleted_at.is_(None),
        ).order_by(Agent.name).all(),
        {"password_hash"},
    )


def list_agents(db: Session, page: int = 1, page_size: int = 20,
                name: Optional[str] = None, type: Optional[int] = None,
                status: Optional[int] = None) -> dict:
    q = db.query(Agent).filter(Agent.deleted_at.is_(None))
    if name:
        q = q.filter(Agent.name.ilike(f"%{name}%"))
    if type is not None:
        q = q.filter(Agent.type == type)
    if status is not None:
        q = q.filter(Agent.status == status)
    total = q.count()
    items = q.order_by(Agent.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": _models_to_dicts(items, {"password_hash"})}


def list_all_agents(db: Session) -> list:
    return _models_to_dicts(
        db.query(Agent).filter(Agent.deleted_at.is_(None)).order_by(Agent.name).all(),
        {"password_hash"},
    )


def get_agent_tree(db: Session) -> list:
    """Build agent tree from parent_id self-referencing structure."""
    agents = db.query(Agent).filter(Agent.deleted_at.is_(None)).order_by(Agent.id).all()
    agent_map = {a.id: {"id": a.id, "name": a.name, "type": a.type,
                        "parent_id": a.parent_id, "status": a.status, "children": []}
                 for a in agents}
    roots = []
    for a in agents:
        node = agent_map[a.id]
        if a.parent_id and a.parent_id in agent_map:
            agent_map[a.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def get_agent_raw(db: Session, id: int) -> Optional[Agent]:
    """Get raw ORM model (not serialized dict)."""
    return db.query(Agent).filter(Agent.id == id, Agent.deleted_at.is_(None)).first()


def get_agent(db: Session, id: int) -> Optional[dict]:
    agent = db.query(Agent).filter(Agent.id == id, Agent.deleted_at.is_(None)).first()
    return _model_to_dict(agent, {"password_hash"})


def create_agent(db: Session, data: AgentCreate) -> dict:
    """创建代理商，带业务校验。
    Java 校验：大代理(type=1)不能有parent，小代理(type=2)必须有parent。
    """
    # 层级校验
    if data.type == 1 and data.parent_id is not None:
        raise ValueError("大代理不能有上级代理")
    if data.type == 2 and data.parent_id is None:
        raise ValueError("小代理必须有上级代理")
    # parent 存在性校验
    if data.parent_id is not None:
        parent = db.query(Agent).filter(Agent.id == data.parent_id, Agent.deleted_at.is_(None)).first()
        if not parent:
            raise ValueError(f"上级代理ID {data.parent_id} 不存在")
    obj = Agent(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj, {"password_hash"})


def update_agent(db: Session, data: AgentUpdate) -> Optional[dict]:
    obj = db.query(Agent).filter(Agent.id == data.id, Agent.deleted_at.is_(None)).first()
    if not obj:
        return None
    # 层级校验（仅当 type 或 parent_id 变更时）
    new_type = data.type if data.type is not None else obj.type
    new_parent_id = data.parent_id if data.parent_id is not None else obj.parent_id
    if new_type == 1 and new_parent_id is not None:
        raise ValueError("大代理不能有上级代理")
    if new_type == 2 and new_parent_id is None:
        raise ValueError("小代理必须有上级代理")
    if new_parent_id is not None:
        parent = db.query(Agent).filter(Agent.id == new_parent_id, Agent.deleted_at.is_(None)).first()
        if not parent:
            raise ValueError(f"上级代理ID {new_parent_id} 不存在")
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj, {"password_hash"})


def delete_agent(db: Session, id: int) -> bool:
    obj = get_agent_raw(db, id)
    if not obj:
        return False
    # Java: 不允许删除还有子代理的代理商
    children = db.query(Agent).filter(
        Agent.parent_id == id, Agent.deleted_at.is_(None)
    ).count()
    if children > 0:
        raise ValueError(f"该代理下有 {children} 个子代理，请先删除子代理")
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def update_agent_status(db: Session, id: int, new_status: int) -> Optional[dict]:
    obj = get_agent_raw(db, id)
    if not obj:
        return None
    obj.status = new_status
    db.commit()
    db.refresh(obj)
    return _model_to_dict(obj, {"password_hash"})


# ============ CommissionConfig ============

def list_commission_configs(db: Session, page=1, page_size=20,
                            effective_month: Optional[str] = None) -> dict:
    q = db.query(CommissionConfig).filter(CommissionConfig.deleted_at.is_(None))
    if effective_month:
        q = q.filter(CommissionConfig.effective_month == effective_month)
    total = q.count()
    items = q.order_by(CommissionConfig.effective_month.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_commission_config(db: Session, id: int) -> Optional[CommissionConfig]:
    return db.query(CommissionConfig).filter(CommissionConfig.id == id, CommissionConfig.deleted_at.is_(None)).first()


def get_current_commission_config(db: Session) -> Optional[CommissionConfig]:
    """Get the most recent active commission config."""
    return db.query(CommissionConfig).filter(
        CommissionConfig.deleted_at.is_(None),
        CommissionConfig.status == 1,
    ).order_by(CommissionConfig.effective_month.desc()).first()


def create_commission_config(db: Session, data: CommissionConfigCreate) -> CommissionConfig:
    obj = CommissionConfig(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_commission_config(db: Session, data: CommissionConfigUpdate) -> Optional[CommissionConfig]:
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


# ============ AgentFee ============

def list_agent_fees(db: Session, page=1, page_size=20,
                    agent_id: Optional[int] = None,
                    fee_month: Optional[str] = None,
                    settlement_status: Optional[int] = None) -> dict:
    q = db.query(AgentFee).filter(AgentFee.deleted_at.is_(None))
    if agent_id is not None:
        q = q.filter(AgentFee.agent_id == agent_id)
    if fee_month:
        q = q.filter(AgentFee.fee_month == fee_month)
    if settlement_status is not None:
        q = q.filter(AgentFee.settlement_status == settlement_status)
    total = q.count()
    items = q.order_by(AgentFee.fee_month.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_agent_fee_statistics(db: Session, agent_id: Optional[int] = None) -> dict:
    q = db.query(AgentFee).filter(AgentFee.deleted_at.is_(None))
    if agent_id is not None:
        q = q.filter(AgentFee.agent_id == agent_id)
    fees = q.all()
    total_amount = sum(float(f.commission_amount or 0) for f in fees)
    settled = sum(float(f.commission_amount or 0) for f in fees if f.settlement_status == 2)
    pending = sum(float(f.commission_amount or 0) for f in fees if f.settlement_status == 1)
    return {
        "total_amount": total_amount,
        "settled_amount": settled,
        "pending_amount": pending,
        "count": len(fees),
    }


def batch_settle_agent_fees(db: Session, ids: list[int], status: int) -> int:
    count = db.query(AgentFee).filter(
        AgentFee.id.in_(ids),
        AgentFee.deleted_at.is_(None),
    ).update({"settlement_status": status, "settlement_date": datetime.now(timezone.utc).date()},
             synchronize_session=False)
    db.commit()
    return count


def reverse_settle_agent_fees(db: Session, ids: list[int]) -> int:
    count = db.query(AgentFee).filter(
        AgentFee.id.in_(ids),
        AgentFee.deleted_at.is_(None),
    ).update({"settlement_status": 1, "settlement_date": None}, synchronize_session=False)
    db.commit()
    return count


def get_agent_fee(db: Session, id: int) -> Optional[AgentFee]:
    return db.query(AgentFee).filter(AgentFee.id == id, AgentFee.deleted_at.is_(None)).first()
