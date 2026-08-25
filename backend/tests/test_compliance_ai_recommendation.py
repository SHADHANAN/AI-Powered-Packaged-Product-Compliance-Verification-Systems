"""Unit tests for the AI-assisted compliance corrective recommendations and constraints."""
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
from app.models.user import User
from app.models.verification import Verification
from app.ai.recommendation import generate_ai_corrective_recommendations
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
        name="Inspector Recommendation AI",
        email="recommendation.inspector@metrology.gov",
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


def test_generate_ai_corrective_recommendations_compliant(db_session: Session, monkeypatch):
    """Test recommendations for a fully compliant product (should be empty)."""
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

    check1 = ComplianceCheck(
        verification_id=verification.id,
        rule_code="LM-001",
        rule_name="Product Name Check",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="Product name is clearly declared."
    )
    db_session.add(check1)
    db_session.commit()

    recs = generate_ai_corrective_recommendations(db_session, verification.id)
    assert len(recs) == 0


def test_generate_ai_corrective_recommendations_non_compliant(db_session: Session, monkeypatch):
    """Test recommendations for a non-compliant product using mock provider."""
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

    recs = generate_ai_corrective_recommendations(db_session, verification.id)

    assert len(recs) == 1
    assert "MRP declaration is missing" in recs[0]["issue"]
    assert "Mock AI Recommendation" in recs[0]["recommendation"]
    assert "Advisory recommendation only" in recs[0]["recommendation"]
    assert recs[0]["confidence"] == 0.95


def test_corrective_recommendation_fallback_disabled(db_session: Session, monkeypatch):
    """Test fallback when AI is disabled."""
    monkeypatch.setenv("AI_ENABLED", "False")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=70.0,
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
        message="Net quantity is unreadable.",
        recommendation="Display Net Quantity clearly."
    )
    db_session.add(check1)
    db_session.commit()

    recs = generate_ai_corrective_recommendations(db_session, verification.id)

    assert len(recs) == 1
    assert recs[0]["issue"] == "Net quantity is unreadable."
    assert "Display Net Quantity clearly." in recs[0]["recommendation"]
    assert "Advisory recommendation only" in recs[0]["recommendation"]
    assert recs[0]["confidence"] == 0.9


def test_corrective_recommendation_fallback_on_ai_failure(db_session: Session, monkeypatch):
    """Test fallback when AI text generator raises an exception."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=80.0,
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
        message="Address is too brief.",
        recommendation="Affix full postal address."
    )
    db_session.add(check1)
    db_session.commit()

    with patch("app.services.ai_service.AIService.generate_text", side_effect=Exception("API failure")):
        recs = generate_ai_corrective_recommendations(db_session, verification.id)

    assert len(recs) == 1
    assert recs[0]["issue"] == "Address is too brief."
    assert "Affix full postal address." in recs[0]["recommendation"]
    assert "Advisory recommendation only" in recs[0]["recommendation"]


def test_api_compliance_recommendations_endpoint(client, db_session: Session, monkeypatch):
    """Test the GET /api/verifications/{id}/compliance/recommendations endpoint."""
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

    response = client.get(f"/api/verifications/{verification.id}/compliance/recommendations")
    assert response.status_code == 200

    data = response.json()
    assert data["verification_id"] == str(verification.id)
    assert len(data["recommendations"]) == 1
    assert "Mock AI Recommendation" in data["recommendations"][0]["recommendation"]
