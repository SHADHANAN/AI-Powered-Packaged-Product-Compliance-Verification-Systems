import io
import uuid
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.compliance_check import ComplianceCheck
from app.models.enums import AuditAction, ComplianceStatus, ReportType, Severity, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.models.verification import Verification
from app.services import audit_service, pdf_report_service, report_service
from app.utils.exceptions import NotFoundException
from app.utils.security import create_access_token, hash_password


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session):
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def secret_password() -> str:
    return "UltraSecretPassphrase987!@"


@pytest.fixture
def inspector_user(db_session: Session, secret_password: str) -> User:
    """Create inspector user with known password."""
    user = User(
        name="Senior Inspector Sharma",
        email="sharma.inspector@metrology.gov.in",
        password_hash=hash_password(secret_password),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_product(db_session: Session) -> Product:
    """Create sample product record."""
    product = Product(
        product_name="Organic Green Tea Infusion",
        brand_name="Himalayan Brews",
        manufacturer="Himalayan Tea Estates Pvt Ltd, Darjeeling, West Bengal 734101",
        country_of_origin="India",
        net_quantity="100 g",
        quantity_unit="g",
        mrp=249.00,
        batch_number="HB-GT-2026-004",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def evaluated_verification(
    db_session: Session,
    inspector_user: User,
    sample_product: Product,
) -> Verification:
    """Create a fully evaluated verification with extracted fields, compliance checks, and report record."""
    verification = Verification(
        product_id=sample_product.id,
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/test_green_tea.jpg",
        status=VerificationStatus.COMPLETED,
        overall_score=83.33,
    )
    db_session.add(verification)
    db_session.commit()

    # Extracted fields
    fields = [
        ExtractedField(
            verification_id=verification.id,
            field_name="mrp",
            field_value="249.00",
            confidence=0.96,
            source_text="MRP Rs. 249.00 (incl. of all taxes)",
        ),
        ExtractedField(
            verification_id=verification.id,
            field_name="net_quantity",
            field_value="100 g",
            confidence=0.92,
            source_text="Net Weight: 100 g",
        ),
        ExtractedField(
            verification_id=verification.id,
            field_name="manufacturer",
            field_value="Himalayan Tea Estates Pvt Ltd, Darjeeling",
            confidence=0.88,
            source_text="Packed by Himalayan Tea Estates",
        ),
    ]
    for f in fields:
        db_session.add(f)

    # Compliance checks (2 PASS, 1 FAIL)
    checks = [
        ComplianceCheck(
            verification_id=verification.id,
            rule_code="LM-MRP-001",
            rule_name="Mandatory MRP Declaration",
            status=ComplianceStatus.PASS,
            severity=Severity.HIGH,
            message="Valid MRP declared: Rs. 249.00",
            expected_value="Positive numeric price",
            actual_value="249.00",
        ),
        ComplianceCheck(
            verification_id=verification.id,
            rule_code="LM-QTY-001",
            rule_name="Net Quantity Declaration",
            status=ComplianceStatus.PASS,
            severity=Severity.CRITICAL,
            message="Valid net quantity declared: 100 g",
            expected_value="Positive quantity with standard unit",
            actual_value="100 g",
        ),
        ComplianceCheck(
            verification_id=verification.id,
            rule_code="LM-CARE-001",
            rule_name="Consumer Care Details Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Consumer helpline contact missing from package label",
            expected_value="Customer care phone or email",
            actual_value=None,
            recommendation="Affix customer care helpline or contact email on the primary display panel.",
        ),
    ]
    for c in checks:
        db_session.add(c)

    # Initial audit logs
    audit_service.create_audit_log(
        db=db_session,
        verification_id=verification.id,
        user_id=inspector_user.id,
        action=AuditAction.IMAGE_UPLOADED,
        status="SUCCESS",
        details="Uploaded product label image",
    )
    audit_service.create_audit_log(
        db=db_session,
        verification_id=verification.id,
        user_id=inspector_user.id,
        action=AuditAction.COMPLIANCE_CHECKED,
        status="SUCCESS",
        details="Rule evaluation score: 83.33%",
    )

    db_session.commit()

    # Generate structured report record
    report_service.generate_compliance_report(
        db=db_session,
        verification_id=verification.id,
        user_id=inspector_user.id,
    )

    db_session.refresh(verification)
    return verification


@pytest.fixture
def auth_headers(inspector_user: User) -> dict:
    """Generate Bearer Authorization header."""
    token = create_access_token(user_id=inspector_user.id, role=inspector_user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. PDF SERVICE UNIT TESTS
# ----------------------------------------------------------------------

def test_generate_compliance_pdf_service(
    db_session: Session,
    evaluated_verification: Verification,
    inspector_user: User,
):
    """Verify PDF service generates valid non-empty PDF bytes and records audit event."""
    pdf_buffer = pdf_report_service.generate_compliance_pdf(
        db=db_session,
        verification_id=evaluated_verification.id,
        user_id=inspector_user.id,
    )
    assert isinstance(pdf_buffer, io.BytesIO)
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")

    # Verify audit event logged
    audit_entries = audit_service.get_verification_audit_logs(db_session, evaluated_verification.id)
    pdf_audit = [a for a in audit_entries if a.action == AuditAction.REPORT_PDF_EXPORTED]
    assert len(pdf_audit) >= 1
    assert pdf_audit[-1].status == "SUCCESS"


def test_generate_pdf_missing_verification(db_session: Session):
    """Verify 404 when verification does not exist."""
    with pytest.raises(NotFoundException):
        pdf_report_service.generate_compliance_pdf(db=db_session, verification_id=uuid.uuid4())


def test_generate_pdf_missing_compliance_report(db_session: Session, inspector_user: User):
    """Verify error when compliance report has not been generated."""
    v = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/unreported.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    with pytest.raises(NotFoundException):
        pdf_report_service.generate_compliance_pdf(db=db_session, verification_id=v.id)


def test_generate_pdf_with_long_text_wrapping(
    db_session: Session,
    inspector_user: User,
):
    """Verify that very long manufacturer address and OCR strings render gracefully without crashing."""
    p = Product(
        product_name="Ultra Long Name " * 15,
        manufacturer="Very Long Industrial Park Address, Building 999, Suite 100, Sector 45, Tech Zone, Greater Metropolis Area, State of Somewhere 999999, Country of Wonderland",
    )
    db_session.add(p)
    db_session.commit()

    v = Verification(
        product_id=p.id,
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/long_text.jpg",
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
    )
    db_session.add(v)
    db_session.commit()

    db_session.add(ExtractedField(
        verification_id=v.id,
        field_name="manufacturer",
        field_value="Super long value text repeated " * 20,
        source_text="Source raw string repeated " * 20,
    ))
    db_session.add(ComplianceCheck(
        verification_id=v.id,
        rule_code="LM-LONG-001",
        rule_name="Long Description Rule " * 5,
        status=ComplianceStatus.PASS,
        severity=Severity.LOW,
        message="A very long explanation of the compliance check outcome that spans across multiple lines " * 10,
        recommendation="Recommendation text repeated for testing page layout stability " * 5,
    ))
    db_session.commit()

    report_service.generate_compliance_report(db=db_session, verification_id=v.id)

    pdf_buffer = pdf_report_service.generate_compliance_pdf(db=db_session, verification_id=v.id)
    assert pdf_buffer.getvalue().startswith(b"%PDF")
    assert len(pdf_buffer.getvalue()) > 1000


# ----------------------------------------------------------------------
# 2. PDF API INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_api_export_pdf_endpoint_success(
    client: TestClient,
    evaluated_verification: Verification,
    auth_headers: dict,
):
    """Test GET /api/verifications/{id}/report/pdf returns 200 with correct headers."""
    v_id = evaluated_verification.id
    response = client.get(f"/api/verifications/{v_id}/report/pdf", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert f'filename="compliance_report_{v_id}.pdf"' in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_api_export_pdf_unauthenticated(
    client: TestClient,
    evaluated_verification: Verification,
):
    """Test 401 when no JWT is supplied."""
    v_id = evaluated_verification.id
    response = client.get(f"/api/verifications/{v_id}/report/pdf")
    assert response.status_code == 401


def test_api_export_pdf_nonexistent_verification(
    client: TestClient,
    auth_headers: dict,
):
    """Test 404 for non-existent verification."""
    random_id = uuid.uuid4()
    response = client.get(f"/api/verifications/{random_id}/report/pdf", headers=auth_headers)
    assert response.status_code == 404


# ----------------------------------------------------------------------
# 3. PDF CONTENT & SECURITY TESTS
# ----------------------------------------------------------------------

def test_pdf_content_and_security_leak_prevention(
    db_session: Session,
    evaluated_verification: Verification,
    inspector_user: User,
    secret_password: str,
    auth_headers: dict,
):
    """Test extracted text content and verify zero credential leakage in generated PDF."""
    pdf_buffer = pdf_report_service.generate_compliance_pdf(
        db=db_session,
        verification_id=evaluated_verification.id,
        user_id=inspector_user.id,
    )
    reader = PdfReader(pdf_buffer)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() or ""

    # 1. Verify expected report content is present
    assert "PACKAGED PRODUCT" in extracted_text
    assert "COMPLIANCE VERIFICATION" in extracted_text
    assert "Organic Green Tea Infusion" in extracted_text
    assert "Senior Inspector Sharma" in extracted_text
    assert "83.3%" in extracted_text or "83.33%" in extracted_text
    assert "LM-MRP-001" in extracted_text
    assert "LM-CARE-001" in extracted_text
    assert "STATUTORY DISCLAIMER" in extracted_text

    # 2. Strict Security Tests: verify NO credentials or secrets leak
    settings = get_settings()
    assert secret_password not in extracted_text
    assert inspector_user.password_hash not in extracted_text
    assert "argon2" not in extracted_text.lower()
    assert settings.JWT_SECRET_KEY not in extracted_text
    assert auth_headers["Authorization"].split()[1] not in extracted_text
    assert "postgresql://" not in extracted_text
    assert "sqlite://" not in extracted_text
    assert "C:\\Users" not in extracted_text
    assert "c:/users" not in extracted_text.lower()
