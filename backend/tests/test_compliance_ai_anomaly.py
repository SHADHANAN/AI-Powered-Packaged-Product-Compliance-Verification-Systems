"""Unit tests for the AI-assisted product label anomaly detection and advisory signals."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.config import get_settings
from app.main import app
from app.models.enums import UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
from app.ai.anomaly import generate_ai_anomaly_detection
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
        name="Inspector Anomaly AI",
        email="anomaly.inspector@metrology.gov",
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


def test_generate_ai_anomalies_detected(db_session: Session, monkeypatch):
    """Test AI detects anomalies for a suspicious label using Mock AI provider."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=75.0,
        ocr_raw_text="The label has anomaly duplicate declaration with Net Qty mismatch.",
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    field1 = ExtractedField(
        verification_id=verification.id,
        field_name="net_quantity",
        field_value="500g",
        confidence=0.95,
        source_text="Net Qty: 500g"
    )
    db_session.add(field1)
    db_session.commit()

    anomalies = generate_ai_anomaly_detection(db_session, verification.id)

    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_detected"] is True
    assert anomalies[0]["anomaly_type"] == "Conflicting Values"
    assert "Mock AI Explanation" in anomalies[0]["explanation"]
    assert "Advisory signal only" in anomalies[0]["explanation"]
    assert anomalies[0]["confidence"] == 0.95


def test_generate_ai_anomalies_clean(db_session: Session, monkeypatch):
    """Test clean label returns empty list."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        ocr_raw_text="Clean product label with standard declarations.",
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    field1 = ExtractedField(
        verification_id=verification.id,
        field_name="mrp",
        field_value="199.00",
        confidence=0.95,
        source_text="MRP: Rs. 199.00"
    )
    field2 = ExtractedField(
        verification_id=verification.id,
        field_name="net_quantity",
        field_value="500g",
        confidence=0.95,
        source_text="Net Qty: 500g"
    )
    field3 = ExtractedField(
        verification_id=verification.id,
        field_name="manufacturer",
        field_value="Fresh Foods Ltd",
        confidence=0.95,
        source_text="Mfg by: Fresh Foods Ltd"
    )
    db_session.add(field1)
    db_session.add(field2)
    db_session.add(field3)
    db_session.commit()

    anomalies = generate_ai_anomaly_detection(db_session, verification.id)
    assert len(anomalies) == 0


def test_anomalies_fallback_disabled(db_session: Session, monkeypatch):
    """Test fallback logic when AI is disabled."""
    monkeypatch.setenv("AI_ENABLED", "False")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=50.0,
        ocr_raw_text="MRP: Free sample not for sale.",
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    field1 = ExtractedField(
        verification_id=verification.id,
        field_name="mrp",
        field_value="Free sample",
        confidence=0.95,
        source_text="MRP: Free sample"
    )
    db_session.add(field1)
    db_session.commit()

    anomalies = generate_ai_anomaly_detection(db_session, verification.id)

    # Missing net_quantity and manufacturer, plus malformed MRP (no digits)
    types = {a["anomaly_type"] for a in anomalies}
    assert "Missing Expected Field" in types
    assert "Malformed Value" in types
    assert all("Advisory signal only" in a["explanation"] for a in anomalies)


def test_anomalies_fallback_on_ai_failure(db_session: Session, monkeypatch):
    """Test fallback when AI call raises an exception."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=90.0,
        ocr_raw_text="Clean product label.",
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    with patch("app.services.ai_service.AIService.generate_text", side_effect=Exception("API failure")):
        anomalies = generate_ai_anomaly_detection(db_session, verification.id)

    # Since AI fails, fallback is triggered. All 3 required fields (mrp, qty, manufacturer) are missing.
    assert len(anomalies) == 3
    assert all(a["anomaly_type"] == "Missing Expected Field" for a in anomalies)


def test_api_label_anomalies_endpoint(client, db_session: Session, monkeypatch):
    """Test the GET /api/verifications/{id}/anomalies endpoint."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=75.0,
        ocr_raw_text="The label has anomaly duplicate declaration with Net Qty mismatch.",
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    field1 = ExtractedField(
        verification_id=verification.id,
        field_name="net_quantity",
        field_value="500g",
        confidence=0.95,
        source_text="Net Qty: 500g"
    )
    db_session.add(field1)
    db_session.commit()

    response = client.get(f"/api/verifications/{verification.id}/anomalies")
    assert response.status_code == 200

    data = response.json()
    assert data["verification_id"] == str(verification.id)
    assert len(data["anomalies"]) == 1
    assert data["anomalies"][0]["anomaly_detected"] is True
    assert data["anomalies"][0]["anomaly_type"] == "Conflicting Values"
    assert "Mock AI Explanation" in data["anomalies"][0]["explanation"]
