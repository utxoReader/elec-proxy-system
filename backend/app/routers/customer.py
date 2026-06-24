"""Customer management routers."""
from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.customer import (
    CustomerAccountCreate, CustomerAccountUpdate,
    CustomerPriceChange, CustomerStatusChange,
)
from app.services import customer as svc

router = APIRouter(prefix="/elec")


@router.get("/customer-account/page", response_model=ApiResponse)
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_name: str = Query(None),
    customer_status: int = Query(None),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.list_customers(db, page, page_size, customer_name, customer_status, agent_id))


@router.get("/customer-account/get/{id}", response_model=ApiResponse)
def get_customer(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.get_customer(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.get("/customer-account/list", response_model=ApiResponse)
def list_customers_no_page(
    customer_name: str = Query(None),
    customer_status: int = Query(None),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.list_customers_no_page(db, customer_name, customer_status, agent_id))


@router.get("/customer-account/list-by-agent", response_model=ApiResponse)
def get_customers_by_agent(
    agent_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.get_customers_by_agent(db, agent_id))


@router.get("/customer-account/list-by-status", response_model=ApiResponse)
def get_customers_by_status(
    customer_status: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.get_customers_by_status(db, customer_status))


@router.get("/customer-account/simple-list", response_model=ApiResponse)
def list_simple_customers(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return ApiResponse(data=svc.list_simple_customers(db))


@router.get("/customer-account/contracted-customers", response_model=ApiResponse)
def list_contracted_customers(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return ApiResponse(data=svc.list_contracted_customers(db))


@router.post("/customer-account/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerAccountCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.create_customer(db, payload)
    return ApiResponse(message="Created", data={"id": obj["id"]})


@router.put("/customer-account/update", response_model=ApiResponse)
def update_customer(payload: CustomerAccountUpdate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_customer(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj["id"]})


@router.delete("/customer-account/delete/{id}", response_model=ApiResponse)
def delete_customer(id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    try:
        ok = svc.delete_customer(db, id)
        if not ok:
            return ApiResponse(success=False, message="Not found")
        return ApiResponse(message="Deleted")
    except ValueError as e:
        return ApiResponse(success=False, message=str(e))


@router.put("/customer-account/update-status", response_model=ApiResponse)
def update_customer_status(payload: CustomerStatusChange, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.update_customer_status(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Status updated", data={"id": obj["id"], "status": obj["customer_status"]})


@router.put("/customer-account/batch-update-status", response_model=ApiResponse)
def batch_update_customer_status(
    ids: str = Query(..., description="Comma-separated IDs"),
    customer_status: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    count = svc.batch_update_customer_status(db, id_list, customer_status)
    return ApiResponse(message=f"Updated {count} records", data={"count": count})


@router.put("/customer-account/sign-contract", response_model=ApiResponse)
def sign_contract(
    id: int = Query(...),
    contract_start_date: str = Query(None, description="YYYY-MM-DD"),
    contract_end_date: str = Query(None, description="YYYY-MM-DD"),
    package_type: str = Query(None),
    price_difference: float = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    from app.schemas.customer import CustomerAccountUpdate
    payload = CustomerAccountUpdate(
        id=id,
        contract_start_date=contract_start_date,
        contract_end_date=contract_end_date,
        package_type=package_type,
        price_difference=price_difference,
    )
    obj = svc.sign_contract(db, id, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Contract signed", data={"id": obj["id"]})


@router.put("/customer-account/terminate-contract", response_model=ApiResponse)
def terminate_contract(
    id: int = Query(...),
    reason: str = Query(...),
    terminate_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.terminate_contract(db, id, reason, terminate_date)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Contract terminated", data={"id": obj["id"]})


@router.put("/customer-account/update-price-and-contract", response_model=ApiResponse)
def change_customer_price(payload: CustomerPriceChange, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    obj = svc.change_customer_price(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Price updated, effective {}".format(payload.effective_date))


# Options
@router.get("/customer-account/options", response_model=ApiResponse)
def get_customer_options(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.get_customer_options(db))


@router.get("/customer-account/count-by-status", response_model=ApiResponse)
def count_customers_by_status(
    customer_status: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    count = svc.count_customers_by_status(db, customer_status)
    return ApiResponse(data={"customer_status": customer_status, "count": count})


# Price history
@router.get("/customer-account/price-history/page", response_model=ApiResponse)
def list_price_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_account_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.list_price_history(db, page, page_size, customer_account_id))


@router.get("/customer-account/export-excel")
def export_customers_excel(
    customer_status: int = Query(None),
    agent_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Export customer accounts as Excel."""
    return svc.export_customers_excel(db, customer_status, agent_id)


@router.get("/customer-account/import-template")
def download_customer_import_template(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Download blank customer import template."""
    return svc.download_customer_import_template()


@router.post("/customer-account/import", response_model=ApiResponse)
def import_customers(file: UploadFile, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Import customer accounts from Excel."""
    result = svc.import_customers_from_excel(db, file)
    return ApiResponse(data=result)
