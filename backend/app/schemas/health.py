from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health-check response."""

    status: str = Field(default="healthy", description="Status of the application service")
    service: str = Field(default="product-compliance-backend", description="Identifier of the service")
