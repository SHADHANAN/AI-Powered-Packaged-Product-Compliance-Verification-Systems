from fastapi import APIRouter, status
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status and identity of the backend service.",
)
async def check_health() -> HealthResponse:
    """Check health status of the service."""
    return HealthResponse(
        status="healthy",
        service="product-compliance-backend",
    )
