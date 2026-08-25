"""Unit tests for the AI-assisted compliance explanations and safety constraints."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.config import get_settings
from app.main import app
from app.models.enums import ComplianceStatus, Severity, UserRole, VerificationStatus
from app.models.compliance_check import ComplianceCheck
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
from app.ai.explanation import generate_ai_compliance_explanation
from app.utils.security import hash_password


@pytest.fixture(autouse=True)
def cleanup_settings():
    """Autouse fixture to reset cache after each test to prevent settings pollution."""
    yield
    get_settings.cache_clear()


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
        name="Inspector Explanation AI",
        email="explanation.inspector@metrology.gov",
        password_hash=hash_password("InspectorPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session, inspector_user):
    """FastAPI TestClient fixture with db and user override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_require_auth():
        return inspector_user

    app.dependency_overrides[get_db] = override_get_db
    from app.api.authorization import require_authenticated_user
    app.dependency_overrides[require_authenticated_user] = override_require_auth

    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def test_generate_ai_compliance_explanation_compliant(db_session: Session, monkeypatch):
    """Test generating compliance explanation for a compliant verification."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    # Create verification
    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    # Add compliance checks (all PASS)
    check1 = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-001",
        rule_name="Product Name Check",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="Product name is clearly declared."
    )
    db_session.add(check1)

    # Add extracted fields
    field1 = ExtractedField(
        verification_id=verification.id,
        field_name="product_name",
        field_value="Premium Tea",
        confidence=0.95,
        source_text="Product Name: Premium Tea"
    )
    db_session.add(field1)
    db_session.commit()

    # Execute service
    res = generate_ai_compliance_explanation(db_session, verification.id)

    assert res["status"] == "COMPLIANT"
    assert res["score"] == 100.0
    assert len(res["violations"]) == 0
    assert "Mock AI" in res["explanation"]
    assert "satisfies all Legal Metrology" in res["explanation"]


def test_generate_ai_compliance_explanation_non_compliant(db_session: Session, monkeypatch):
    """Test generating compliance explanation for a non-compliant verification."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=70.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    # Add a FAIL check
    check1 = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-MRP-001",
        rule_name="MRP Declaration Check",
        status=ComplianceStatus.FAIL,
        severity=Severity.CRITICAL,
        message="MRP is missing."
    )
    db_session.add(check1)
    db_session.commit()

    res = generate_ai_compliance_explanation(db_session, verification.id)

    assert res["status"] == "NON_COMPLIANT"
    assert res["score"] == 70.0
    assert len(res["violations"]) == 1
    assert "LM-MRP-001" in res["violations"][0]
    assert "failed compliance verification" in res["explanation"]


def test_compliance_explanation_fallback_disabled(db_session: Session, monkeypatch):
    """Test fallback when AI is disabled."""
    monkeypatch.setenv("AI_ENABLED", "False")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=75.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    check1 = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-QTY-001",
        rule_name="Net Quantity Check",
        status=ComplianceStatus.FAIL,
        severity=Severity.HIGH,
        message="Net quantity unit is invalid."
    )
    db_session.add(check1)
    db_session.commit()

    res = generate_ai_compliance_explanation(db_session, verification.id)

    assert res["status"] == "NON_COMPLIANT"
    # Fallback explanation should be constructed locally
    assert "The product is non-compliant" in res["explanation"]
    assert "Net quantity unit is invalid" in res["explanation"]


def test_compliance_explanation_fallback_on_ai_failure(db_session: Session, monkeypatch):
    """Test fallback when AI service call raises an exception."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=90.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    check1 = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-WARN-001",
        rule_name="Warning Check",
        status=ComplianceStatus.WARNING,
        severity=Severity.MEDIUM,
        message="OCR confidence is low."
    )
    db_session.add(check1)
    db_session.commit()

    # Mock AIService to raise Exception
    with patch("app.services.ai_service.AIService.generate_text", side_effect=Exception("API Error")):
        res = generate_ai_compliance_explanation(db_session, verification.id)

    assert res["status"] == "PARTIALLY_COMPLIANT"
    assert "requires manual verification" in res["explanation"]


def test_compliance_explanation_fallback_on_safety_contradiction(db_session: Session, monkeypatch):
    """Test fallback when AI returns non-compliant output for a COMPLIANT product."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    # Mock AIService to return a response containing "non-compliant"
    with patch("app.services.ai_service.AIService.generate_text", return_value="The product is non-compliant"):
        res = generate_ai_compliance_explanation(db_session, verification.id)

    # Should trigger fallback since status is COMPLIANT but AI output says non-compliant
    assert res["status"] == "COMPLIANT"
    assert "fully compliant with all evaluated" in res["explanation"]


def test_api_compliance_explain_endpoint(client, db_session: Session, monkeypatch):
    """Test the GET /api/verifications/{id}/compliance/explain endpoint."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    response = client.get(f"/api/verifications/{verification.id}/compliance/explain")
    assert response.status_code == 200

    data = response.json()
    assert data["verification_id"] == str(verification.id)
    assert data["status"] == "COMPLIANT"
    assert "Mock AI" in data["explanation"]
