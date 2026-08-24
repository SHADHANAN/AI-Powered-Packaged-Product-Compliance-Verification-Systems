"""Pydantic schemas for data validation and API response serialization."""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorDetail, ErrorResponse, RootResponse
from app.schemas.compliance_check import (
    ComplianceCheckBase,
    ComplianceCheckCreate,
    ComplianceCheckRead,
)
from app.schemas.extracted_field import (
    ExtractedFieldBase,
    ExtractedFieldCreate,
    ExtractedFieldRead,
)
from app.schemas.health import DatabaseHealthResponse, HealthResponse
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.schemas.report import (
    ReportBase,
    ReportCreate,
    ReportRead,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.schemas.verification import (
    VerificationBase,
    VerificationCreate,
    VerificationRead,
    VerificationUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    # Common & Health
    "HealthResponse",
    "DatabaseHealthResponse",
    "RootResponse",
    "ErrorDetail",
    "ErrorResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    # Product
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductRead",
    # Verification
    "VerificationBase",
    "VerificationCreate",
    "VerificationUpdate",
    "VerificationRead",
    # ExtractedField
    "ExtractedFieldBase",
    "ExtractedFieldCreate",
    "ExtractedFieldRead",
    # ComplianceCheck
    "ComplianceCheckBase",
    "ComplianceCheckCreate",
    "ComplianceCheckRead",
    # Report
    "ReportBase",
    "ReportCreate",
    "ReportRead",
]
