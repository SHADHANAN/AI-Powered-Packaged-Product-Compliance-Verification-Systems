import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ComplianceStatus, ReportType, Severity, UserRole, VerificationStatus


class ReportBase(BaseModel):
    """Base schema for exported verification report."""

    verification_id: uuid.UUID
    report_type: ReportType = ReportType.PDF
    file_path: str = Field(..., max_length=1000)


class ReportCreate(ReportBase):
    """Schema for recording generated report file."""
    pass


class ReportRead(ReportBase):
    """Schema for reading report database record."""

    id: uuid.UUID
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# STRUCTURED COMPLIANCE REPORT SCHEMAS
# ----------------------------------------------------------------------

class ReportProductInfo(BaseModel):
    """Product metadata included in compliance report."""

    id: uuid.UUID
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    importer: Optional[str] = None
    country_of_origin: Optional[str] = None
    net_quantity: Optional[str] = None
    quantity_unit: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    import_date: Optional[date] = None
    mrp: Optional[float] = None
    customer_care_details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReportInspectorInfo(BaseModel):
    """Inspector identity included in compliance report (strictly no password/secrets)."""

    id: uuid.UUID
    name: str
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class ReportField(BaseModel):
    """Extracted label field details in report."""

    field_name: str
    field_value: str
    confidence: Optional[float] = None
    source_text: Optional[str] = None


class ReportCheck(BaseModel):
    """Individual rule check outcome in report."""

    rule_code: str
    rule_name: str
    status: ComplianceStatus
    severity: Severity
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    recommendation: Optional[str] = None


class ReportViolation(BaseModel):
    """Structured violation item."""

    rule_code: str
    rule_name: str
    severity: Severity
    status: ComplianceStatus
    affected_field: Optional[str] = None
    detected_value: Optional[str] = None
    expected_requirement: Optional[str] = None
    recommendation: Optional[str] = None


class ReportSummary(BaseModel):
    """Summary statistics for compliance report."""

    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    not_applicable_rules: int = 0
    overall_score: Optional[float] = None


class ComplianceReportData(BaseModel):
    """Full structured compliance report payload for API responses and export."""

    report_id: Optional[uuid.UUID] = None
    verification_id: uuid.UUID
    generated_at: datetime
    verification_status: VerificationStatus
    overall_score: Optional[float] = None
    product: Optional[ReportProductInfo] = None
    inspector: Optional[ReportInspectorInfo] = None
    summary: ReportSummary
    extracted_fields: List[ReportField] = []
    checks: List[ReportCheck] = []
    violations: List[ReportViolation] = []
    recommendations: List[str] = []

    model_config = ConfigDict(from_attributes=True)
