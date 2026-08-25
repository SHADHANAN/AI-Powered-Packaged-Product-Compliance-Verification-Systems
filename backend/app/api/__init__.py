from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.compliance_checks import router as compliance_checks_router
from app.api.extracted_fields import router as extracted_fields_router
from app.api.extraction import router as extraction_router
from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.reports import router as reports_router
from app.api.users import router as users_router
from app.api.verifications import router as verifications_router

api_router = APIRouter()

# Health endpoints
api_router.include_router(health_router)

# Authentication endpoints
api_router.include_router(auth_router, prefix="/auth")

# Core CRUD endpoints
api_router.include_router(users_router, prefix="/users")
api_router.include_router(products_router, prefix="/products")
api_router.include_router(verifications_router, prefix="/verifications")
api_router.include_router(extracted_fields_router, prefix="/extracted-fields")
api_router.include_router(extraction_router, prefix="/extraction")
api_router.include_router(compliance_checks_router, prefix="/compliance-checks")
api_router.include_router(reports_router, prefix="/reports")

__all__ = [
    "api_router",
    "health_router",
    "auth_router",
    "users_router",
    "products_router",
    "verifications_router",
    "extracted_fields_router",
    "extraction_router",
    "compliance_checks_router",
    "reports_router",
]
