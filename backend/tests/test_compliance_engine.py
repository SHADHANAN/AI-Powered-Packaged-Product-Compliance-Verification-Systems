import uuid
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.compliance_check import ComplianceCheck
from app.models.enums import ComplianceStatus, Severity, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
from app.services import compliance_engine
from app.services.compliance_rules import RuleEvaluationResult
from app.utils.exceptions import NotFoundException
from app.utils.security import hash_password


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
def inspector_user(db_session: Session) -> User:
    """Create inspector user."""
    user = User(
        name="Inspector Compliance",
        email="compliance.inspector@metrology.gov",
        password_hash=hash_password("InspectorPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_calculate_compliance_score_bounds():
    """Test score calculation helper logic and weighting."""
    # All Pass -> 100%
    results_all_pass = [
        RuleEvaluationResult("R1", "Rule 1", ComplianceStatus.PASS, Severity.HIGH, "ok"),
        RuleEvaluationResult("R2", "Rule 2", ComplianceStatus.PASS, Severity.CRITICAL, "ok"),
    ]
    assert compliance_engine.calculate_compliance_score(results_all_pass) == 100.0

    # All Fail -> 0%
    results_all_fail = [
        RuleEvaluationResult("R1", "Rule 1", ComplianceStatus.FAIL, Severity.HIGH, "fail"),
        RuleEvaluationResult("R2", "Rule 2", ComplianceStatus.FAIL, Severity.CRITICAL, "fail"),
    ]
    assert compliance_engine.calculate_compliance_score(results_all_fail) == 0.0

    # Mixed with Warning and Not Applicable
    results_mixed = [
        RuleEvaluationResult("R1", "Rule 1", ComplianceStatus.PASS, Severity.CRITICAL, "ok"),  # 4 * 1.0 = 4 / 4
        RuleEvaluationResult("R2", "Rule 2", ComplianceStatus.WARNING, Severity.HIGH, "warn"), # 3 * 0.5 = 1.5 / 3
        RuleEvaluationResult("R3", "Rule 3", ComplianceStatus.FAIL, Severity.MEDIUM, "fail"),  # 2 * 0.0 = 0 / 2
        RuleEvaluationResult("R4", "Rule 4", ComplianceStatus.NOT_APPLICABLE, Severity.HIGH, "na"), # excluded
    ]
    # Total applicable = 4 + 3 + 2 = 9
    # Passed = 4 + 1.5 + 0 = 5.5
    # Score = (5.5 / 9) * 100 = 61.11%
    score = compliance_engine.calculate_compliance_score(results_mixed)
    assert score == 61.11


def test_evaluate_verification_compliance_fully_compliant(db_session: Session, inspector_user: User):
    """Test compliance evaluation on a fully compliant set of extracted fields."""
    verification = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/sample.jpg",
        status=VerificationStatus.PROCESSING,
    )
    db_session.add(verification)
    db_session.commit()

    sample_fields = [
        ("product_name", "Organic Rolled Oats"),
        ("brand_name", "OatPure"),
        ("manufacturer", "OatPure India Foods Ltd, Bangalore 560001"),
        ("country_of_origin", "India"),
        ("net_quantity", "1 kg"),
        ("quantity_unit", "kg"),
        ("mrp", "250.00"),
        ("batch_number", "BATCH-OP-102"),
        ("manufacturing_date", "09/2024"),
        ("customer_care_details", "support@oatpure.in / 1800-444-5555"),
    ]
    for name, val in sample_fields:
        db_session.add(ExtractedField(
            verification_id=verification.id,
            field_name=name,
            field_value=val,
            confidence=0.9,
            source_text=f"{name}: {val}",
        ))
    db_session.commit()

    summary = compliance_engine.evaluate_verification_compliance(db_session, verification.id)

    assert summary.total_rules >= 10
    assert summary.passed_rules >= 9
    assert summary.failed_rules == 0
    assert summary.overall_score is not None
    assert summary.overall_score >= 95.0
    assert summary.status == VerificationStatus.COMPLETED

    # Check persistence
    checks = db_session.query(ComplianceCheck).filter(ComplianceCheck.verification_id == verification.id).all()
    assert len(checks) == summary.total_rules


def test_compliance_evaluation_idempotence(db_session: Session, inspector_user: User):
    """Ensure running compliance evaluation multiple times does not duplicate records."""
    verification = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/sample.jpg",
        status=VerificationStatus.PROCESSING,
    )
    db_session.add(verification)
    db_session.commit()

    db_session.add(ExtractedField(
        verification_id=verification.id,
        field_name="mrp",
        field_value="100.00",
        confidence=0.95,
        source_text="MRP: 100",
    ))
    db_session.commit()

    # First run
    summary1 = compliance_engine.evaluate_verification_compliance(db_session, verification.id)
    count1 = db_session.query(ComplianceCheck).filter(ComplianceCheck.verification_id == verification.id).count()

    # Second run
    summary2 = compliance_engine.evaluate_verification_compliance(db_session, verification.id)
    count2 = db_session.query(ComplianceCheck).filter(ComplianceCheck.verification_id == verification.id).count()

    assert count1 == count2
    assert summary1.total_rules == summary2.total_rules


def test_compliance_evaluation_nonexistent_verification(db_session: Session):
    """Ensure evaluating a nonexistent verification raises NotFoundException."""
    with pytest.raises(NotFoundException):
        compliance_engine.evaluate_verification_compliance(db_session, uuid.uuid4())
