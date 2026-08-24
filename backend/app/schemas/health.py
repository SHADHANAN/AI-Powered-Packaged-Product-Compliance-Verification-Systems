from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for standard service health-check response."""

    status: str = Field(default="healthy", description="Status of the application service")
    service: str = Field(default="product-compliance-backend", description="Identifier of the service")


class DatabaseHealthResponse(BaseModel):
    """Schema for database health-check response."""

    status: str = Field(..., description="Connectivity status of the database (connected/disconnected)")
    database: str = Field(default="postgresql", description="Database engine type")
