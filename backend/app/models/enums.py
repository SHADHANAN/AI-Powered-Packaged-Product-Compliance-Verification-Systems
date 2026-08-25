import enum


class UserRole(str, enum.Enum):
    """User account role."""
    ADMIN = "admin"
    INSPECTOR = "inspector"
    VIEWER = "viewer"


class VerificationStatus(str, enum.Enum):
    """Status lifecycle of a compliance verification run."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplianceStatus(str, enum.Enum):
    """Outcome status of an individual compliance rule check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


class Severity(str, enum.Enum):
    """Severity level of a compliance check non-conformity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(str, enum.Enum):
    """Supported export report formats."""
    PDF = "pdf"
    EXCEL = "excel"


class AuditAction(str, enum.Enum):
    """Action tracked in the verification audit trail."""
    IMAGE_UPLOADED = "IMAGE_UPLOADED"
    OCR_PROCESSED = "OCR_PROCESSED"
    FIELDS_EXTRACTED = "FIELDS_EXTRACTED"
    COMPLIANCE_CHECKED = "COMPLIANCE_CHECKED"
    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_PDF_EXPORTED = "REPORT_PDF_EXPORTED"
    SECURITY_ALERT = "SECURITY_ALERT"
