import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ComplianceStatus, Severity, VerificationStatus


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


class ComplianceSummaryRead(BaseModel):
    """Aggregated compliance evaluation summary for a verification run."""

    verification_id: uuid.UUID
    overall_score: Optional[float] = None
    status: VerificationStatus
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    not_applicable_rules: int = 0
    violations: List[ComplianceCheckRead] = []
    recommendations: List[str] = []
    checks: List[ComplianceCheckRead] = []
    ai_status: Optional[str] = None
    fallback_used: Optional[bool] = None
    decision_source: Optional[str] = None
    final_result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
