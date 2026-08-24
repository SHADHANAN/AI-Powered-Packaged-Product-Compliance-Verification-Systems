import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    ComplianceStatus,
    ReportType,
    Severity,
    UserRole,
    VerificationStatus,
)
from app.schemas import (
    ComplianceCheckCreate,
    ExtractedFieldCreate,
    ProductCreate,
    ReportCreate,
    UserCreate,
    VerificationCreate,
)
from app.services import (
    compliance_check_service,
    extracted_field_service,
    product_service,
    report_service,
    user_service,
    verification_service,
)
from app.utils.exceptions import BadRequestException, NotFoundException


@pytest.fixture
def db_session():
    """Create a fresh SQLite in-memory database session for testing services."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_user_service_crud(db_session: Session):
    """Test User service Create, Read, List, Delete, and Not Found."""
    # 1. Create
    user_in = UserCreate(
        name="Test User",
        email="test@user.com",
        password="secretpassword123",
        role=UserRole.INSPECTOR,
    )
    user = user_service.create_user(db_session, user_in)
    assert user.id is not None
    assert user.email == "test@user.com"

    # Duplicate email check
    with pytest.raises(BadRequestException):
        user_service.create_user(db_session, user_in)

    # 2. Get by ID
    fetched = user_service.get_user(db_session, user.id)
    assert fetched.id == user.id

    # 3. List
    users = user_service.get_users(db_session)
    assert len(users) == 1

    # 4. Delete
    user_service.delete_user(db_session, user.id)
    with pytest.raises(NotFoundException):
        user_service.get_user(db_session, user.id)

    # Delete non-existent
    with pytest.raises(NotFoundException):
        user_service.delete_user(db_session, uuid.uuid4())


def test_product_service_crud(db_session: Session):
    """Test Product service Create, Read, List, Delete, and Not Found."""
    prod_in = ProductCreate(
        product_name="Corn Flakes 500g",
        brand_name="Kellogg",
        mrp=Decimal("199.00"),
    )
    product = product_service.create_product(db_session, prod_in)
    assert product.id is not None
    assert product.product_name == "Corn Flakes 500g"

    # Get by ID
    fetched = product_service.get_product(db_session, product.id)
    assert fetched.product_name == "Corn Flakes 500g"

    # List
    products = product_service.get_products(db_session)
    assert len(products) == 1

    # Delete
    product_service.delete_product(db_session, product.id)
    with pytest.raises(NotFoundException):
        product_service.get_product(db_session, product.id)


def test_verification_service_crud(db_session: Session):
    """Test Verification service Create, Read, List, Delete, and Not Found."""
    v_in = VerificationCreate(
        source_image_path="uploads/images/sample.png",
    )
    verification = verification_service.create_verification(db_session, v_in)
    assert verification.id is not None
    assert verification.status == VerificationStatus.PENDING

    # Get by ID
    fetched = verification_service.get_verification(db_session, verification.id)
    assert fetched.id == verification.id

    # List
    v_list = verification_service.get_verifications(db_session)
    assert len(v_list) == 1

    # Delete
    verification_service.delete_verification(db_session, verification.id)
    with pytest.raises(NotFoundException):
        verification_service.get_verification(db_session, verification.id)


def test_extracted_field_service_crud(db_session: Session):
    """Test ExtractedField service Create, Read, List, Delete, and Not Found."""
    # Create parent verification
    v = verification_service.create_verification(
        db_session, VerificationCreate(source_image_path="sample.jpg")
    )

    field_in = ExtractedFieldCreate(
        verification_id=v.id,
        field_name="net_quantity",
        field_value="500 g",
        confidence=0.95,
        source_text="NET QTY: 500g",
    )
    field = extracted_field_service.create_extracted_field(db_session, field_in)
    assert field.id is not None
    assert field.field_name == "net_quantity"

    # Get by ID
    fetched = extracted_field_service.get_extracted_field(db_session, field.id)
    assert fetched.field_value == "500 g"

    # List
    fields = extracted_field_service.get_extracted_fields(db_session)
    assert len(fields) == 1

    # Delete
    extracted_field_service.delete_extracted_field(db_session, field.id)
    with pytest.raises(NotFoundException):
        extracted_field_service.get_extracted_field(db_session, field.id)


def test_compliance_check_service_crud(db_session: Session):
    """Test ComplianceCheck service Create, Read, List, Delete, and Not Found."""
    v = verification_service.create_verification(
        db_session, VerificationCreate(source_image_path="sample.jpg")
    )

    check_in = ComplianceCheckCreate(
        verification_id=v.id,
        rule_code="LM_NET_QUANTITY",
        rule_name="Net Quantity Rule",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="Quantity is compliant",
    )
    check = compliance_check_service.create_compliance_check(db_session, check_in)
    assert check.id is not None
    assert check.rule_code == "LM_NET_QUANTITY"

    # Get by ID
    fetched = compliance_check_service.get_compliance_check(db_session, check.id)
    assert fetched.status == ComplianceStatus.PASS

    # List
    checks = compliance_check_service.get_compliance_checks(db_session)
    assert len(checks) == 1

    # Delete
    compliance_check_service.delete_compliance_check(db_session, check.id)
    with pytest.raises(NotFoundException):
        compliance_check_service.get_compliance_check(db_session, check.id)


def test_report_service_crud(db_session: Session):
    """Test Report service Create, Read, List, Delete, and Not Found."""
    v = verification_service.create_verification(
        db_session, VerificationCreate(source_image_path="sample.jpg")
    )

    report_in = ReportCreate(
        verification_id=v.id,
        report_type=ReportType.PDF,
        file_path="reports/test.pdf",
    )
    report = report_service.create_report(db_session, report_in)
    assert report.id is not None
    assert report.report_type == ReportType.PDF

    # Get by ID
    fetched = report_service.get_report(db_session, report.id)
    assert fetched.file_path == "reports/test.pdf"

    # List
    reports = report_service.get_reports(db_session)
    assert len(reports) == 1

    # Delete
    report_service.delete_report(db_session, report.id)
    with pytest.raises(NotFoundException):
        report_service.get_report(db_session, report.id)
