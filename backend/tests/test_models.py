import uuid
from datetime import datetime
from decimal import Decimal
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    ComplianceCheck,
    ComplianceStatus,
    ExtractedField,
    Product,
    Report,
    ReportType,
    Severity,
    User,
    UserRole,
    Verification,
    VerificationStatus,
)
from app.schemas import (
    ComplianceCheckCreate,
    ComplianceCheckRead,
    ExtractedFieldCreate,
    ExtractedFieldRead,
    ProductCreate,
    ProductRead,
    ReportCreate,
    ReportRead,
    UserCreate,
    UserRead,
    VerificationCreate,
    VerificationRead,
)


def test_models_metadata_registration():
    """Verify all 6 model tables are registered in Base.metadata."""
    table_names = Base.metadata.tables.keys()
    expected_tables = {
        "users",
        "products",
        "verifications",
        "extracted_fields",
        "compliance_checks",
        "reports",
    }
    for expected in expected_tables:
        assert expected in table_names, f"Table '{expected}' is missing from Base.metadata"


def test_user_model_columns_and_constraints():
    """Verify User model columns, unique constraints, and indexes."""
    user_table = Base.metadata.tables["users"]
    assert "id" in user_table.c
    assert "email" in user_table.c
    assert "password_hash" in user_table.c
    assert "role" in user_table.c
    assert "is_active" in user_table.c
    assert "created_at" in user_table.c
    assert "updated_at" in user_table.c
    assert user_table.c.email.unique is True or any(
        idx.unique and "email" in [col.name for col in idx.columns]
        for idx in user_table.indexes
    )


def test_product_model_columns():
    """Verify Product model columns and types."""
    prod_table = Base.metadata.tables["products"]
    assert "id" in prod_table.c
    assert "product_name" in prod_table.c
    assert "brand_name" in prod_table.c
    assert "mrp" in prod_table.c
    assert "manufacturing_date" in prod_table.c


def test_verification_model_constraints():
    """Verify Verification model constraints and foreign keys."""
    v_table = Base.metadata.tables["verifications"]
    assert "overall_score" in v_table.c
    check_constraints = [c.name for c in v_table.constraints if hasattr(c, "name")]
    assert "ck_verification_overall_score" in check_constraints

    fk_targets = {fk.target_fullname for fk in v_table.foreign_keys}
    assert "products.id" in fk_targets
    assert "users.id" in fk_targets


def test_extracted_field_model_constraints():
    """Verify ExtractedField constraints and verification FK."""
    ef_table = Base.metadata.tables["extracted_fields"]
    check_constraints = [c.name for c in ef_table.constraints if hasattr(c, "name")]
    assert "ck_extracted_field_confidence" in check_constraints

    fk_targets = {fk.target_fullname for fk in ef_table.foreign_keys}
    assert "verifications.id" in fk_targets


def test_compliance_check_model_columns():
    """Verify ComplianceCheck columns and verification FK."""
    cc_table = Base.metadata.tables["compliance_checks"]
    assert "rule_code" in cc_table.c
    assert "status" in cc_table.c
    assert "severity" in cc_table.c
    assert "message" in cc_table.c

    fk_targets = {fk.target_fullname for fk in cc_table.foreign_keys}
    assert "verifications.id" in fk_targets


def test_report_model_columns():
    """Verify Report model columns and verification FK."""
    r_table = Base.metadata.tables["reports"]
    assert "report_type" in r_table.c
    assert "file_path" in r_table.c
    assert "generated_at" in r_table.c

    fk_targets = {fk.target_fullname for fk in r_table.foreign_keys}
    assert "verifications.id" in fk_targets


def test_in_memory_orm_relationships():
    """Test creating instances and relationship navigation in an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # 1. Create User
    inspector = User(
        name="Inspector Alice",
        email="alice@inspection.gov",
        password_hash="hashed_secret",
        role=UserRole.INSPECTOR,
    )
    session.add(inspector)

    # 2. Create Product
    product = Product(
        product_name="Organic Almond Milk 1L",
        brand_name="NutriLife",
        mrp=Decimal("250.00"),
    )
    session.add(product)
    session.flush()

    # 3. Create Verification linked to Product & User
    verification = Verification(
        product_id=product.id,
        inspector_id=inspector.id,
        status=VerificationStatus.COMPLETED,
        overall_score=92.5,
        source_image_path="uploads/samples/sample1.jpg",
        ocr_raw_text="NutriLife Organic Almond Milk MRP Rs 250.00",
    )
    session.add(verification)
    session.flush()

    # 4. Add ExtractedField
    extracted = ExtractedField(
        verification_id=verification.id,
        field_name="mrp",
        field_value="250.00",
        confidence=0.98,
        source_text="MRP Rs 250.00",
    )
    session.add(extracted)

    # 5. Add ComplianceCheck
    check = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM_MRP_DECLARATION",
        rule_name="Mandatory MRP Declaration Check",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="MRP declaration is compliant with Legal Metrology rules",
    )
    session.add(check)

    # 6. Add Report
    report = Report(
        verification_id=verification.id,
        report_type=ReportType.PDF,
        file_path="reports/inspection_report_001.pdf",
    )
    session.add(report)
    session.commit()

    # Query and test relationship navigation
    v = session.query(Verification).filter_by(id=verification.id).first()
    assert v is not None
    assert v.inspector.name == "Inspector Alice"
    assert v.product.product_name == "Organic Almond Milk 1L"
    assert len(v.extracted_fields) == 1
    assert v.extracted_fields[0].field_name == "mrp"
    assert len(v.compliance_checks) == 1
    assert v.compliance_checks[0].rule_code == "LM_MRP_DECLARATION"
    assert len(v.reports) == 1
    assert v.reports[0].report_type == ReportType.PDF

    session.close()


def test_pydantic_schemas_validation():
    """Verify validation behaviors of Pydantic schemas."""
    # Valid UserCreate
    user_data = UserCreate(
        name="Bob Smith",
        email="bob@compliance.org",
        password="secretpassword123",
        role=UserRole.ADMIN,
    )
    assert user_data.email == "bob@compliance.org"

    # Invalid email in UserCreate
    with pytest.raises(ValidationError):
        UserCreate(name="Bad", email="invalid-email", password="123")

    # Valid ProductCreate
    prod_data = ProductCreate(
        product_name="Biscuits 200g",
        mrp=Decimal("35.50"),
    )
    assert prod_data.mrp == Decimal("35.50")

    # Score bounds in VerificationCreate / VerificationRead
    with pytest.raises(ValidationError):
        VerificationBase_Test = VerificationRead(
            id=uuid.uuid4(),
            source_image_path="img.jpg",
            overall_score=150.0,  # Invalid: > 100
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # Confidence bounds in ExtractedFieldRead
    with pytest.raises(ValidationError):
        ExtractedFieldRead(
            id=uuid.uuid4(),
            verification_id=uuid.uuid4(),
            field_name="brand",
            confidence=1.5,  # Invalid: > 1.0
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
