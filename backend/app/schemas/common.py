from typing import Any, Optional
from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Schema for root endpoint response."""

    message: str = Field(..., description="Welcome status message")
    app_name: str = Field(..., description="Name of the application")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment mode")
    docs_url: str = Field(..., description="Interactive API documentation URL")


class ErrorDetail(BaseModel):
    """Schema for structured error response."""

    message: str = Field(..., description="Human-readable error description")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Any] = Field(default=None, description="Detailed validation or context information")


class ErrorResponse(BaseModel):
    """Standardized error envelope."""

    success: bool = Field(default=False, description="Operation success flag")
    error: ErrorDetail = Field(..., description="Error payload")
