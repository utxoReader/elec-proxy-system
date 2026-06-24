"""Price management routers.

Covers 5 price tables:
- BasePrice (基础分时电价)
- GridPrice (电网电价)
- WholesalePrice (批发价)
- MarketAllocationPrice (市场分摊价)
- OtherFee (其他费用)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.price import (
    BasePriceCreate, BasePriceUpdate,
    GridPriceCreate, GridPriceUpdate,
    WholesalePriceCreate, WholesalePriceUpdate,
    MarketAllocationCreate, MarketAllocationUpdate,
    OtherFeeCreate, OtherFeeUpdate,
)
from app.services import price as svc

router = APIRouter(prefix="/elec")


# ==================== BasePrice ====================

@router.get("/base-price/page", response_model=ApiResponse)
def list_base_prices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    price_date: str = Query(None, description="YYYY-MM-DD"),
    price_type: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_base_prices(db, page, page_size, price_date, price_type)
    return ApiResponse(data=result)


@router.get("/base-price/get/{id}", response_model=ApiResponse)
def get_base_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_base_price(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/base-price/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_base_price(payload: BasePriceCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_base_price(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/base-price/update", response_model=ApiResponse)
def update_base_price(payload: BasePriceUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_base_price(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/base-price/delete/{id}", response_model=ApiResponse)
def delete_base_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = svc.delete_base_price(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.get("/base-price/list", response_model=ApiResponse)
def list_base_prices_no_page(
    price_type: int = Query(None),
    price_date: str = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_base_prices_no_page(db, price_type, price_date)
    return ApiResponse(data=items)


@router.get("/base-price/list-by-type-and-date", response_model=ApiResponse)
def list_base_prices_by_type_and_date(
    price_type: int = Query(...),
    price_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_base_prices_by_type_and_date(db, price_type, price_date)
    return ApiResponse(data=items)


@router.get("/base-price/monthly-price", response_model=ApiResponse)
def get_monthly_base_prices(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_monthly_base_prices(db, year, month)
    return ApiResponse(data=items)


@router.get("/base-price/flat-rate-price", response_model=ApiResponse)
def get_flat_rate_price(
    price_type: int = Query(...),
    price_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.get_flat_rate_price(db, price_type, price_date)
    return ApiResponse(data=result)


# Note: calculate-flat-rate-price removed — duplicate of flat-rate-price endpoint


@router.post("/base-price/batch-import", response_model=ApiResponse)
def batch_import_base_price(
    payload: list[BasePriceCreate],
    overwrite: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """批量导入基准价（支持覆盖模式）"""
    if overwrite and payload:
        # 验证所有记录有相同的日期和类型（批量导入一次只处理一个日期+类型组合）
        date_type_set = set((str(p.price_date), p.price_type) for p in payload)
        if len(date_type_set) > 1:
            return ApiResponse(success=False, message="All items must share the same price_date and price_type for batch overwrite")
        first_date, first_type = next(iter(date_type_set))
        svc.delete_base_prices_by_date_type(db, first_date, first_type)
    count = svc.batch_create_base_prices(db, payload)
    return ApiResponse(message=f"Imported {count} records", data={"count": count})


# ==================== GridPrice ====================

@router.get("/grid-price/page", response_model=ApiResponse)
def list_grid_prices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year_month: str = Query(None, description="YYYY-MM"),
    time_period: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_grid_prices(db, page, page_size, year_month, time_period)
    return ApiResponse(data=result)


@router.get("/grid-price/get/{id}", response_model=ApiResponse)
def get_grid_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_grid_price(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/grid-price/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_grid_price(payload: GridPriceCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_grid_price(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/grid-price/update", response_model=ApiResponse)
def update_grid_price(payload: GridPriceUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_grid_price(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/grid-price/delete/{id}", response_model=ApiResponse)
def delete_grid_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = svc.delete_grid_price(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.get("/grid-price/list", response_model=ApiResponse)
def list_grid_prices_no_page(
    year_month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_grid_prices_no_page(db, year_month)
    return ApiResponse(data=items)


@router.get("/grid-price/list-by-year-month", response_model=ApiResponse)
def get_grid_prices_by_year_month(
    year_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_grid_prices_by_year_month(db, year_month)
    return ApiResponse(data=items)


@router.post("/grid-price/batch-config", response_model=ApiResponse)
def batch_config_grid_price(
    year_month: str = Query(..., description="YYYY-MM"),
    base_price: float = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    from decimal import Decimal
    created = svc.batch_config_grid_price(db, year_month, Decimal(str(base_price)))
    return ApiResponse(message=f"Configured {len(created)} periods", data={"count": len(created)})


# ==================== WholesalePrice ====================

@router.get("/wholesale-price/page", response_model=ApiResponse)
def list_wholesale_prices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    price_date: str = Query(None),
    price_month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_wholesale_prices(db, page, page_size, price_date, price_month)
    return ApiResponse(data=result)


@router.get("/wholesale-price/get/{id}", response_model=ApiResponse)
def get_wholesale_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_wholesale_price(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/wholesale-price/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_wholesale_price(payload: WholesalePriceCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_wholesale_price(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/wholesale-price/update", response_model=ApiResponse)
def update_wholesale_price(payload: WholesalePriceUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_wholesale_price(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/wholesale-price/delete/{id}", response_model=ApiResponse)
def delete_wholesale_price(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = svc.delete_wholesale_price(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.get("/wholesale-price/list", response_model=ApiResponse)
def list_wholesale_prices_no_page(
    price_date: str = Query(None, description="YYYY-MM-DD"),
    price_month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_wholesale_prices_no_page(db, price_date, price_month)
    return ApiResponse(data=items)


@router.get("/wholesale-price/list-by-date", response_model=ApiResponse)
def get_wholesale_prices_by_date(
    price_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_wholesale_prices_by_date(db, price_date)
    return ApiResponse(data=items)


@router.get("/wholesale-price/calculate-monthly-average", response_model=ApiResponse)
def calculate_wholesale_monthly_average(
    price_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.calculate_wholesale_monthly_average(db, price_month)
    return ApiResponse(data=result)


@router.get("/wholesale-price/price-statistics", response_model=ApiResponse)
def get_wholesale_price_statistics(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.get_wholesale_price_statistics(db, start_date, end_date)
    return ApiResponse(data=result)


@router.post("/wholesale-price/batch-import", response_model=ApiResponse)
def batch_import_wholesale_price(
    payload: list[WholesalePriceCreate],
    overwrite: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """批量导入批发价格"""
    if overwrite and payload:
        date_type_set = set((str(p.price_date), p.price_type) for p in payload)
        if len(date_type_set) > 1:
            return ApiResponse(success=False, message="All items must share the same price_date and price_type for batch overwrite")
        first_date, first_type = next(iter(date_type_set))
        svc.delete_wholesale_prices_by_date(db, first_date, first_type)
    count = svc.batch_create_wholesale_prices(db, payload)
    return ApiResponse(message=f"Imported {count} records", data={"count": count})


# ==================== MarketAllocationPrice ====================

@router.get("/market-allocation/page", response_model=ApiResponse)
def list_market_allocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year_month: str = Query(None, description="YYYY-MM"),
    status: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_market_allocations(db, page, page_size, year_month, status)
    return ApiResponse(data=result)


@router.get("/market-allocation/get/{id}", response_model=ApiResponse)
def get_market_allocation(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_market_allocation(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/market-allocation/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_market_allocation(payload: MarketAllocationCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_market_allocation(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/market-allocation/update", response_model=ApiResponse)
def update_market_allocation(payload: MarketAllocationUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_market_allocation(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/market-allocation/delete/{id}", response_model=ApiResponse)
def delete_market_allocation(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = svc.delete_market_allocation(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.put("/market-allocation/update-status", response_model=ApiResponse)
def update_market_allocation_status(id: int = Query(...), status: int = Query(...), db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_market_allocation_status(db, id, status)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Status updated")


@router.get("/market-allocation/get-by-year-month", response_model=ApiResponse)
def get_market_allocation_by_year_month(
    year_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.get_market_allocation_by_year_month(db, year_month)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/market-allocation/get-allocation-price", response_model=ApiResponse)
def get_allocation_price_value(
    year_month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    price = svc.get_allocation_price_value(db, year_month)
    return ApiResponse(data={"year_month": year_month, "allocation_price": price})


@router.put("/market-allocation/enable/{id}", response_model=ApiResponse)
def enable_market_allocation(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.enable_market_allocation(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Enabled")


@router.put("/market-allocation/disable/{id}", response_model=ApiResponse)
def disable_market_allocation(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.disable_market_allocation(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Disabled")


@router.put("/market-allocation/batch-update-status", response_model=ApiResponse)
def batch_update_market_allocation_status(
    ids: str = Query(..., description="Comma-separated IDs"),
    status: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    count = svc.batch_update_market_allocation_status(db, id_list, status)
    return ApiResponse(message=f"Updated {count} records", data={"count": count})


# ==================== OtherFee ====================

@router.get("/other-fee/page", response_model=ApiResponse)
def list_other_fees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    month_config: str = Query(None, description="YYYY-MM"),
    status: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = svc.list_other_fees(db, page, page_size, month_config, status)
    return ApiResponse(data=result)


@router.get("/other-fee/get/{id}", response_model=ApiResponse)
def get_other_fee(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_other_fee(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/other-fee/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_other_fee(payload: OtherFeeCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_other_fee(db, payload)
    return ApiResponse(message="Created", data={"id": obj.id})


@router.put("/other-fee/update", response_model=ApiResponse)
def update_other_fee(payload: OtherFeeUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_other_fee(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj.id})


@router.delete("/other-fee/delete/{id}", response_model=ApiResponse)
def delete_other_fee(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ok = svc.delete_other_fee(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.put("/other-fee/update-status", response_model=ApiResponse)
def update_other_fee_status(id: int = Query(...), status: int = Query(...), db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_other_fee_status(db, id, status)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Status updated")


@router.get("/other-fee/list-enabled", response_model=ApiResponse)
def list_enabled_other_fees(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_enabled_other_fees(db)
    return ApiResponse(data=items)


@router.get("/other-fee/get-by-month", response_model=ApiResponse)
def get_other_fee_by_month(
    month_config: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.get_other_fee_by_month(db, month_config)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)
