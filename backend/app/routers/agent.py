"""Agent management routers.

Covers:
- Agent CRUD + tree + status
- Note: CommissionConfig and AgentFee moved to commission router (#13)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services import agent as svc

router = APIRouter(prefix="/elec")


# ==================== Agent ====================

@router.get("/agent/page", response_model=ApiResponse)
def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = Query(None),
    type: int = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.list_agents(db, page, page_size, name, type, status))


@router.get("/agent/list", response_model=ApiResponse)
def list_all_agents(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.list_all_agents(db))


@router.get("/agent/list-by-parent", response_model=ApiResponse)
def get_agents_by_parent(
    parent_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_agents_by_parent(db, parent_id)
    return ApiResponse(data=items)


@router.get("/agent/list-by-type", response_model=ApiResponse)
def get_agents_by_type(
    type: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.get_agents_by_type(db, type)
    return ApiResponse(data=items)


@router.get("/agent/options", response_model=ApiResponse)
def get_agent_options(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items = svc.list_all_agents(db)
    return ApiResponse(data=items)


@router.get("/agent/tree", response_model=ApiResponse)
def get_agent_tree(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return ApiResponse(data=svc.get_agent_tree(db))


@router.get("/agent/get/{id}", response_model=ApiResponse)
def get_agent(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.get_agent(db, id)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(data=obj)


@router.post("/agent/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.create_agent(db, payload)
    return ApiResponse(message="Created", data={"id": obj["id"]})


@router.put("/agent/update", response_model=ApiResponse)
def update_agent(
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.update_agent(db, payload)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Updated", data={"id": obj["id"]})


@router.delete("/agent/delete/{id}", response_model=ApiResponse)
def delete_agent(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    ok = svc.delete_agent(db, id)
    if not ok:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Deleted")


@router.put("/agent/update-status", response_model=ApiResponse)
def update_agent_status(
    id: int = Query(...),
    status: int = Query(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = svc.update_agent_status(db, id, status)
    if not obj:
        return ApiResponse(success=False, message="Not found")
    return ApiResponse(message="Status updated")

