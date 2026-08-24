import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ComplianceStatus, Severity


class ComplianceCheckBase(BaseModel):
    """Base schema for compliance check evaluation result."""

    verification_id: uuid.UUID
    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=255)
    status: ComplianceStatus
    severity: Severity
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    recommendation: Optional[str] = None


class ComplianceCheckCreate(ComplianceCheckBase):
    """Schema for persisting a compliance check result."""
    pass


class ComplianceCheckRead(ComplianceCheckBase):
    """Schema for reading compliance check result."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
