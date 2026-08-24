from fastapi import APIRouter, status
from app.database import check_db_connection
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status and identity of the backend service.",
)
async def check_health() -> HealthResponse:
    """Check overall service health status (Phase 1 contract)."""
    return HealthResponse(
        status="healthy",
        service="product-compliance-backend",
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Database Connectivity Check",
    description="Returns whether PostgreSQL database is currently reachable.",
)
async def check_database_health() -> DatabaseHealthResponse:
    """Check database connection without throwing unhandled exceptions."""
    is_connected = check_db_connection()
    return DatabaseHealthResponse(
        status="connected" if is_connected else "disconnected",
        database="postgresql",
    )
