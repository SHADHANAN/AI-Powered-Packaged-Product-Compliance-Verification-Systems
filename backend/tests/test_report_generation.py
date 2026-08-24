import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.compliance_check import ComplianceCheck
from app.models.enums import ComplianceStatus, Severity, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.product import Product
from app.models.user import User
from app.models.verification import Verification
from app.services import report_service
from app.utils.exceptions import BadRequestException, NotFoundException
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
def inspector_user(db_session: Session) -> User:
    """Create inspector user."""
    user = User(
        name="Report Inspector",
        email="report.inspector@metrology.gov",
        password_hash=hash_password("InspectorSecret123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_product(db_session: Session) -> Product:
    """Create product record."""
    product = Product(
        product_name="Premium Almond Cookies",
        brand_name="NutriBite",
        manufacturer="NutriBite Foods Ltd, Bangalore",
        country_of_origin="India",
        net_quantity="200 g",
        quantity_unit="g",
        mrp=150.00,
        batch_number="NB-2024-01",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def evaluated_verification(db_session: Session, inspector_user: User, sample_product: Product) -> Verification:
    """Create a fully evaluated verification with fields and compliance checks."""
    verification = Verification(
        product_id=sample_product.id,
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/report_sample.jpg",
        status=VerificationStatus.COMPLETED,
        overall_score=85.0,
    )
    db_session.add(verification)
    db_session.commit()

    # Add Extracted Fields
    db_session.add(ExtractedField(
        verification_id=verification.id,
        field_name="mrp",
        field_value="150.00",
        confidence=0.95,
        source_text="MRP Rs. 150.00",
    ))
    db_session.add(ExtractedField(
        verification_id=verification.id,
        field_name="net_quantity",
        field_value="200 g",
        confidence=0.90,
        source_text="Net Qty: 200 g",
    ))

    # Add Compliance Checks (1 pass, 1 fail)
    db_session.add(ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-MRP-001",
        rule_name="Mandatory MRP Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="Valid MRP declared: Rs. 150.00",
        expected_value="Positive numeric price",
        actual_value="150.00",
    ))
    db_session.add(ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-CARE-001",
        rule_name="Consumer Care Details Declaration",
        status=ComplianceStatus.FAIL,
        severity=Severity.HIGH,
        message="Consumer care details missing",
        expected_value="Contact info",
        actual_value=None,
        recommendation="Include consumer helpline or email",
    ))
    db_session.commit()
    db_session.refresh(verification)
    return verification


@pytest.fixture
def auth_headers(inspector_user: User) -> dict:
    """Generate Bearer Authorization header."""
    token = create_access_token(user_id=inspector_user.id, role=inspector_user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. REPORT SERVICE UNIT TESTS
# ----------------------------------------------------------------------

def test_generate_compliance_report_service(db_session: Session, evaluated_verification: Verification, inspector_user: User):
    """Test generating a structured report via report_service."""
    report = report_service.generate_compliance_report(
        db=db_session,
        verification_id=evaluated_verification.id,
        user_id=inspector_user.id,
    )
    assert report.verification_id == evaluated_verification.id
    assert report.overall_score == 85.0
    assert report.summary.total_rules == 2
    assert report.summary.passed_rules == 1
    assert report.summary.failed_rules == 1
    assert len(report.extracted_fields) == 2
    assert len(report.checks) == 2
    assert len(report.violations) == 1
    assert report.violations[0].rule_code == "LM-CARE-001"
    assert report.inspector is not None
    assert report.inspector.email == inspector_user.email
    assert not hasattr(report.inspector, "password_hash")


def test_generate_report_idempotency(db_session: Session, evaluated_verification: Verification):
    """Ensure regenerating report updates existing record instead of creating duplicates."""
    report1 = report_service.generate_compliance_report(db=db_session, verification_id=evaluated_verification.id)
    report2 = report_service.generate_compliance_report(db=db_session, verification_id=evaluated_verification.id)

    assert report1.report_id == report2.report_id
    assert report1.verification_id == report2.verification_id


def test_generate_report_fails_on_unevaluated_verification(db_session: Session, inspector_user: User):
    """Ensure generating report fails if compliance checks have not run."""
    v = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/sample.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    with pytest.raises(BadRequestException):
        report_service.generate_compliance_report(db=db_session, verification_id=v.id)


def test_generate_report_nonexistent_verification(db_session: Session):
    """Ensure generating report for nonexistent verification raises NotFoundException."""
    with pytest.raises(NotFoundException):
        report_service.generate_compliance_report(db=db_session, verification_id=uuid.uuid4())


# ----------------------------------------------------------------------
# 2. REPORT API INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_api_report_endpoints_workflow(
    client: TestClient,
    evaluated_verification: Verification,
    auth_headers: dict,
):
    """Test POST & GET /api/verifications/{id}/report endpoints."""
    v_id = evaluated_verification.id

    # 1. Unauthorized checks
    assert client.post(f"/api/verifications/{v_id}/report").status_code == 401
    assert client.get(f"/api/verifications/{v_id}/report").status_code == 401

    # 2. Non-existent verification check
    random_id = uuid.uuid4()
    assert client.post(f"/api/verifications/{random_id}/report", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{random_id}/report", headers=auth_headers).status_code == 404

    # 3. Generate Report (POST)
    post_res = client.post(f"/api/verifications/{v_id}/report", headers=auth_headers)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["verification_id"] == str(v_id)
    assert data["overall_score"] == 85.0
    assert data["summary"]["total_rules"] == 2
    assert len(data["violations"]) == 1
    assert "password_hash" not in str(data)

    # 4. Get Report (GET)
    get_res = client.get(f"/api/verifications/{v_id}/report", headers=auth_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["verification_id"] == str(v_id)
    assert get_data["report_id"] == data["report_id"]
