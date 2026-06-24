"""Price management business logic."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.price import (
    BasePrice, GridPrice, WholesalePrice, MarketAllocationPrice, OtherFee,
)
from app.schemas.price import (
    BasePriceCreate, BasePriceUpdate,
    GridPriceCreate, GridPriceUpdate,
    WholesalePriceCreate, WholesalePriceUpdate,
    MarketAllocationCreate, MarketAllocationUpdate,
    OtherFeeCreate, OtherFeeUpdate,
)


# ========== BasePrice ==========
def list_base_prices(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    price_date: Optional[str] = None,
    price_type: Optional[int] = None,
) -> dict:
    q = db.query(BasePrice).filter(BasePrice.deleted_at.is_(None))
    if price_date:
        q = q.filter(BasePrice.price_date == price_date)
    if price_type is not None:
        q = q.filter(BasePrice.price_type == price_type)
    total = q.count()
    items = q.order_by(BasePrice.price_date.desc(), BasePrice.hour_index.asc()) \
              .offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def list_base_prices_no_page(db: Session, price_type: Optional[int] = None, price_date: Optional[str] = None) -> list:
    """获取基准价列表（无分页）"""
    q = db.query(BasePrice).filter(BasePrice.deleted_at.is_(None))
    if price_type is not None:
        q = q.filter(BasePrice.price_type == price_type)
    if price_date:
        q = q.filter(BasePrice.price_date == price_date)
    return q.order_by(BasePrice.price_date.desc(), BasePrice.hour_index.asc()).all()


def get_base_prices_by_type_and_date(db: Session, price_type: int, price_date: str) -> list:
    """根据类型和日期获取24小时基准价"""
    return db.query(BasePrice).filter(
        BasePrice.deleted_at.is_(None),
        BasePrice.price_type == price_type,
        BasePrice.price_date == price_date,
    ).order_by(BasePrice.hour_index.asc()).all()


def get_monthly_base_prices(db: Session, year: int, month: int) -> list:
    """获取某年月的基准价（用于询价）"""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    from datetime import date
    start = date(year, month, 1)
    end = date(year, month, last_day)
    return db.query(BasePrice).filter(
        BasePrice.deleted_at.is_(None),
        BasePrice.price_date >= start,
        BasePrice.price_date <= end,
    ).order_by(BasePrice.price_date.asc(), BasePrice.hour_index.asc()).all()


def batch_create_base_prices(db: Session, items: list[BasePriceCreate]) -> int:
    """批量创建基准价（Excel导入用）"""
    count = 0
    for data in items:
        obj = BasePrice(**data.model_dump())
        db.add(obj)
        count += 1
    db.commit()
    return count


def delete_base_prices_by_date_type(db: Session, price_date: str, price_type: int) -> int:
    """删除指定日期和类型的基准价（覆盖导入前清理）"""
    from datetime import datetime, timezone
    rows = db.query(BasePrice).filter(
        BasePrice.price_date == price_date,
        BasePrice.price_type == price_type,
        BasePrice.deleted_at.is_(None),
    ).all()
    now = datetime.now(timezone.utc)
    for r in rows:
        r.deleted_at = now
    db.commit()
    return len(rows)


def get_flat_rate_price(db: Session, price_type: int, price_date: str) -> dict:
    """计算一口价基准价（24小时加权平均价）"""
    prices = get_base_prices_by_type_and_date(db, price_type, price_date)
    if not prices:
        return {"price_type": price_type, "price_date": price_date, "flat_rate_price": None, "hour_count": 0}
    total = sum(p.price for p in prices if p.price)
    count = len([p for p in prices if p.price])
    if count == 0:
        return {"price_type": price_type, "price_date": price_date, "flat_rate_price": None, "hour_count": 0}
    return {
        "price_type": price_type,
        "price_date": price_date,
        "flat_rate_price": total / count,
        "hour_count": count,
    }


def get_base_price(db: Session, id: int) -> Optional[BasePrice]:
    return db.query(BasePrice).filter(BasePrice.id == id, BasePrice.deleted_at.is_(None)).first()


def create_base_price(db: Session, data: BasePriceCreate) -> BasePrice:
    obj = BasePrice(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_base_price(db: Session, data: BasePriceUpdate) -> Optional[BasePrice]:
    obj = get_base_price(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_base_price(db: Session, id: int) -> bool:
    obj = get_base_price(db, id)
    if not obj:
        return False
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ========== GridPrice ==========
def list_grid_prices(db: Session, page=1, page_size=20, year_month: Optional[str] = None, time_period: Optional[int] = None) -> dict:
    q = db.query(GridPrice).filter(GridPrice.deleted_at.is_(None))
    if year_month:
        q = q.filter(GridPrice.year_month == year_month)
    if time_period is not None:
        q = q.filter(GridPrice.time_period == time_period)
    total = q.count()
    items = q.order_by(GridPrice.year_month.desc(), GridPrice.time_period.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def list_grid_prices_no_page(db: Session, year_month: Optional[str] = None) -> list:
    """获取电网价格列表（无分页）"""
    q = db.query(GridPrice).filter(GridPrice.deleted_at.is_(None))
    if year_month:
        q = q.filter(GridPrice.year_month == year_month)
    return q.order_by(GridPrice.year_month.desc(), GridPrice.time_period.asc()).all()


def get_grid_prices_by_year_month(db: Session, year_month: str) -> list:
    """根据年月获取电网价格"""
    return db.query(GridPrice).filter(
        GridPrice.deleted_at.is_(None),
        GridPrice.year_month == year_month,
    ).order_by(GridPrice.time_period.asc()).all()


def batch_config_grid_price(db: Session, year_month: str, base_price: Decimal) -> list:
    """批量配置某年月的电网价格（4个时段统一基准价）"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # 删除已存在的该年月记录
    existing = db.query(GridPrice).filter(
        GridPrice.year_month == year_month,
        GridPrice.deleted_at.is_(None),
    ).all()
    for e in existing:
        e.deleted_at = now
    
    # 生成标准时段配置（匹配原系统 PriceUtils.generateStandardTimePeriodConfigs）
    from datetime import time as dttime
    month = int(year_month.split("-")[1])
    is_peak = month in {1, 7, 8, 12}  # 尖峰期月份
    coeffs = {1: Decimal("1.92"), 2: Decimal("1.60"), 3: Decimal("1.00"), 4: Decimal("0.45")}
    
    period_configs = [
        # (time_period, start_time, end_time)
        (4, dttime(0, 0), dttime(6, 59, 59)),       # 低谷 00:00-06:59
        (3, dttime(7, 0), dttime(7, 59, 59)),        # 平时 07:00-07:59
        (2, dttime(8, 0), dttime(9, 59, 59)),        # 高峰 08:00-09:59
        (3, dttime(10, 0), dttime(10, 59, 59)),      # 平时 10:00-10:59
        (4, dttime(11, 0), dttime(12, 59, 59)),      # 低谷 11:00-12:59
        (3, dttime(13, 0), dttime(16, 59, 59)),      # 平时 13:00-16:59
        (2, dttime(17, 0), dttime(17, 59, 59)),      # 高峰 17:00-17:59
    ]
    
    # 18:00-19:59 取决于是否为尖峰月
    if is_peak:
        period_configs.append((1, dttime(18, 0), dttime(19, 59, 59)))  # 尖峰 18:00-19:59
    else:
        period_configs.append((2, dttime(18, 0), dttime(19, 59, 59)))  # 高峰 18:00-19:59
    
    period_configs.extend([
        (2, dttime(20, 0), dttime(22, 59, 59)),      # 高峰 20:00-22:59
        (3, dttime(23, 0), dttime(23, 59, 59)),      # 平时 23:00-23:59
    ])
    
    created = []
    for tp, st, et in period_configs:
        c = coeffs[tp]
        obj = GridPrice(
            year_month=year_month,
            time_period=tp,
            start_time=st,
            end_time=et,
            base_price=base_price,
            price_coefficient=c,
            price=base_price * c,
            status=0,
        )
        db.add(obj)
        created.append(obj)
    db.commit()
    for o in created:
        db.refresh(o)
    return created


def get_grid_price(db: Session, id: int) -> Optional[GridPrice]:
    return db.query(GridPrice).filter(GridPrice.id == id, GridPrice.deleted_at.is_(None)).first()


def create_grid_price(db: Session, data: GridPriceCreate) -> GridPrice:
    obj = GridPrice(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_grid_price(db: Session, data: GridPriceUpdate) -> Optional[GridPrice]:
    obj = get_grid_price(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_grid_price(db: Session, id: int) -> bool:
    obj = get_grid_price(db, id)
    if not obj:
        return False
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ========== WholesalePrice ==========
def list_wholesale_prices(db: Session, page=1, page_size=20, price_date: Optional[str] = None, price_month: Optional[str] = None) -> dict:
    q = db.query(WholesalePrice).filter(WholesalePrice.deleted_at.is_(None))
    if price_date:
        q = q.filter(WholesalePrice.price_date == price_date)
    if price_month:
        q = q.filter(WholesalePrice.price_month == price_month)
    total = q.count()
    items = q.order_by(WholesalePrice.price_date.desc(), WholesalePrice.hour_index.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def list_wholesale_prices_no_page(db: Session, price_date: Optional[str] = None, price_month: Optional[str] = None) -> list:
    """获取批发价列表（无分页）"""
    q = db.query(WholesalePrice).filter(WholesalePrice.deleted_at.is_(None))
    if price_date:
        q = q.filter(WholesalePrice.price_date == price_date)
    if price_month:
        q = q.filter(WholesalePrice.price_month == price_month)
    return q.order_by(WholesalePrice.price_date.desc(), WholesalePrice.hour_index.asc()).all()


def get_wholesale_prices_by_date(db: Session, price_date: str) -> list:
    """根据日期获取24小时批发价格"""
    return db.query(WholesalePrice).filter(
        WholesalePrice.deleted_at.is_(None),
        WholesalePrice.price_date == price_date,
    ).order_by(WholesalePrice.hour_index.asc()).all()


def calculate_wholesale_monthly_average(db: Session, price_month: str) -> list[dict]:
    """计算月度平均批发价格（逐小时平均）"""
    from sqlalchemy import func as sa_func
    rows = db.query(
        WholesalePrice.hour_index,
        sa_func.avg(WholesalePrice.wholesale_price).label('avg_price'),
        sa_func.count(WholesalePrice.id).label('day_count'),
    ).filter(
        WholesalePrice.deleted_at.is_(None),
        WholesalePrice.price_month == price_month,
        WholesalePrice.wholesale_price.isnot(None),
    ).group_by(WholesalePrice.hour_index).order_by(WholesalePrice.hour_index.asc()).all()
    
    result = []
    for row in rows:
        result.append({
            "hour_index": row.hour_index,
            "avg_price": float(row.avg_price),
            "day_count": row.day_count,
        })
    return result


def get_wholesale_price_statistics(db: Session, start_date: str, end_date: str) -> dict:
    """获取批发价格统计信息"""
    from sqlalchemy import func as sa_func
    stats = db.query(
        sa_func.min(WholesalePrice.wholesale_price).label('min_price'),
        sa_func.max(WholesalePrice.wholesale_price).label('max_price'),
        sa_func.avg(WholesalePrice.wholesale_price).label('avg_price'),
        sa_func.count(WholesalePrice.id).label('total_count'),
    ).filter(
        WholesalePrice.deleted_at.is_(None),
        WholesalePrice.price_date >= start_date,
        WholesalePrice.price_date <= end_date,
        WholesalePrice.wholesale_price.isnot(None),
    ).first()
    
    # 逐日平均
    daily = db.query(
        WholesalePrice.price_date,
        sa_func.avg(WholesalePrice.wholesale_price).label('daily_avg'),
    ).filter(
        WholesalePrice.deleted_at.is_(None),
        WholesalePrice.price_date >= start_date,
        WholesalePrice.price_date <= end_date,
        WholesalePrice.wholesale_price.isnot(None),
    ).group_by(WholesalePrice.price_date).order_by(WholesalePrice.price_date.asc()).all()
    
    return {
        "min_price": float(stats.min_price) if stats.min_price else None,
        "max_price": float(stats.max_price) if stats.max_price else None,
        "avg_price": float(stats.avg_price) if stats.avg_price else None,
        "total_count": stats.total_count,
        "daily_averages": [{"date": str(r.price_date), "avg": float(r.daily_avg)} for r in daily],
    }


def batch_create_wholesale_prices(db: Session, items: list) -> int:
    """批量创建批发价格（Excel导入用）
    items: list of WholesalePriceCreate
    """
    count = 0
    for data in items:
        obj = WholesalePrice(**data.model_dump())
        db.add(obj)
        count += 1
    db.commit()
    return count


def delete_wholesale_prices_by_date(db: Session, price_date: str, price_type: Optional[int] = None) -> int:
    """删除指定日期的批发价（覆盖导入前清理）"""
    from datetime import datetime, timezone
    q = db.query(WholesalePrice).filter(
        WholesalePrice.price_date == price_date,
        WholesalePrice.deleted_at.is_(None),
    )
    if price_type is not None:
        q = q.filter(WholesalePrice.price_type == price_type)
    rows = q.all()
    now = datetime.now(timezone.utc)
    for r in rows:
        r.deleted_at = now
    db.commit()
    return len(rows)


def get_wholesale_price(db: Session, id: int) -> Optional[WholesalePrice]:
    return db.query(WholesalePrice).filter(WholesalePrice.id == id, WholesalePrice.deleted_at.is_(None)).first()


def create_wholesale_price(db: Session, data: WholesalePriceCreate) -> WholesalePrice:
    obj = WholesalePrice(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_wholesale_price(db: Session, data: WholesalePriceUpdate) -> Optional[WholesalePrice]:
    obj = get_wholesale_price(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_wholesale_price(db: Session, id: int) -> bool:
    obj = get_wholesale_price(db, id)
    if not obj:
        return False
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ========== MarketAllocationPrice ==========
def list_market_allocations(db: Session, page=1, page_size=20, year_month: Optional[str] = None, status: Optional[int] = None) -> dict:
    q = db.query(MarketAllocationPrice).filter(MarketAllocationPrice.deleted_at.is_(None))
    if year_month:
        q = q.filter(MarketAllocationPrice.year_month == year_month)
    if status is not None:
        q = q.filter(MarketAllocationPrice.status == status)
    total = q.count()
    items = q.order_by(MarketAllocationPrice.year_month.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_market_allocation_by_year_month(db: Session, year_month: str) -> Optional[MarketAllocationPrice]:
    """根据年月获取市场分摊价"""
    return db.query(MarketAllocationPrice).filter(
        MarketAllocationPrice.deleted_at.is_(None),
        MarketAllocationPrice.year_month == year_month,
    ).first()


def get_allocation_price_value(db: Session, year_month: str) -> Optional[Decimal]:
    """获取市场分摊单价（仅返回金额）"""
    obj = db.query(MarketAllocationPrice).filter(
        MarketAllocationPrice.deleted_at.is_(None),
        MarketAllocationPrice.year_month == year_month,
    ).first()
    return obj.allocation_price if obj else None


def enable_market_allocation(db: Session, id: int) -> Optional[MarketAllocationPrice]:
    """启用市场分摊价"""
    return update_market_allocation_status(db, id, 0)


def disable_market_allocation(db: Session, id: int) -> Optional[MarketAllocationPrice]:
    """禁用市场分摊价"""
    return update_market_allocation_status(db, id, 1)


def batch_update_market_allocation_status(db: Session, ids: list[int], status: int) -> int:
    """批量更新市场分摊价状态"""
    rows = db.query(MarketAllocationPrice).filter(
        MarketAllocationPrice.id.in_(ids),
        MarketAllocationPrice.deleted_at.is_(None),
    ).all()
    for r in rows:
        r.status = status
    db.commit()
    return len(rows)


def get_market_allocation(db: Session, id: int) -> Optional[MarketAllocationPrice]:
    return db.query(MarketAllocationPrice).filter(MarketAllocationPrice.id == id, MarketAllocationPrice.deleted_at.is_(None)).first()


def create_market_allocation(db: Session, data: MarketAllocationCreate) -> MarketAllocationPrice:
    obj = MarketAllocationPrice(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_market_allocation(db: Session, data: MarketAllocationUpdate) -> Optional[MarketAllocationPrice]:
    obj = get_market_allocation(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_market_allocation(db: Session, id: int) -> bool:
    obj = get_market_allocation(db, id)
    if not obj:
        return False
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def update_market_allocation_status(db: Session, id: int, status: int) -> Optional[MarketAllocationPrice]:
    obj = get_market_allocation(db, id)
    if not obj:
        return None
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


# ========== OtherFee ==========
def list_other_fees(db: Session, page=1, page_size=20, month_config: Optional[str] = None, status: Optional[int] = None) -> dict:
    q = db.query(OtherFee).filter(OtherFee.deleted_at.is_(None))
    if month_config:
        q = q.filter(OtherFee.month_config == month_config)
    if status is not None:
        q = q.filter(OtherFee.status == status)
    total = q.count()
    items = q.order_by(OtherFee.month_config.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def list_enabled_other_fees(db: Session) -> list:
    """获取启用状态的其他费用列表"""
    return db.query(OtherFee).filter(
        OtherFee.deleted_at.is_(None),
        OtherFee.status == 0,
    ).order_by(OtherFee.month_config.desc()).all()


def get_other_fee_by_month(db: Session, month_config: str) -> Optional[OtherFee]:
    """根据月份获取其他费用"""
    return db.query(OtherFee).filter(
        OtherFee.deleted_at.is_(None),
        OtherFee.month_config == month_config,
    ).first()


def get_other_fee(db: Session, id: int) -> Optional[OtherFee]:
    return db.query(OtherFee).filter(OtherFee.id == id, OtherFee.deleted_at.is_(None)).first()


def create_other_fee(db: Session, data: OtherFeeCreate) -> OtherFee:
    obj = OtherFee(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_other_fee(db: Session, data: OtherFeeUpdate) -> Optional[OtherFee]:
    obj = get_other_fee(db, data.id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude={"id"}, exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_other_fee(db: Session, id: int) -> bool:
    obj = get_other_fee(db, id)
    if not obj:
        return False
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def update_other_fee_status(db: Session, id: int, status: int) -> Optional[OtherFee]:
    obj = get_other_fee(db, id)
    if not obj:
        return None
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj
