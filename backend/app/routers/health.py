"""Health check router."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> ApiResponse[dict]:
    """Return a simple health status for load balancers and monitoring."""
    return ApiResponse(data={"status": "ok"})
