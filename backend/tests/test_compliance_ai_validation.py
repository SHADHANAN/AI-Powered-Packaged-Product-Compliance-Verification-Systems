"""Unit tests for the AI-vs-deterministic compliance validation comparison layer."""
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
from app.ai.validation import validate_ai_vs_deterministic
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
        name="Inspector Validation AI",
        email="validation.inspector@metrology.gov",
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


def _add_compliant_fields(db_session: Session, verification_id):
    """Add mandatory fields configured to pass deterministic rules."""
    fields = [
        ExtractedField(verification_id=verification_id, field_name="mrp", field_value="Rs. 199.00"),
        ExtractedField(verification_id=verification_id, field_name="net_quantity", field_value="500 g"),
        ExtractedField(verification_id=verification_id, field_name="quantity_unit", field_value="g"),
        ExtractedField(verification_id=verification_id, field_name="manufacturer", field_value="Fresh Foods Ltd"),
        ExtractedField(verification_id=verification_id, field_name="manufacturer_address", field_value="123 Street, City"),
        ExtractedField(verification_id=verification_id, field_name="manufacturing_date", field_value="08/2026"),
        ExtractedField(verification_id=verification_id, field_name="customer_care_details", field_value="Phone: 1800-123-456, email@care.com"),
        ExtractedField(verification_id=verification_id, field_name="product_name", field_value="Vanilla Custard Powder"),
        ExtractedField(verification_id=verification_id, field_name="brand_name", field_value="Freshy"),
        ExtractedField(verification_id=verification_id, field_name="country_of_origin", field_value="India"),
        ExtractedField(verification_id=verification_id, field_name="batch_number", field_value="B-12345"),
    ]
    for f in fields:
        db_session.add(f)
    db_session.commit()


def test_validation_both_compliant(db_session: Session, monkeypatch):
    """Case 1: Both engines find the product COMPLIANT."""
    monkeypatch.setenv("AI_ENABLED", "True")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    _add_compliant_fields(db_session, verification.id)

    with patch("app.services.ai_service.AIService.evaluate_compliance", return_value=[]):
        res = validate_ai_vs_deterministic(db_session, verification.id)

    assert res["deterministic_result"] == "COMPLIANT"
    assert res["ai_result"] == "COMPLIANT"
    assert res["agreement"] is True
    assert res["final_result"] == "COMPLIANT"
    assert res["review_required"] is False
    assert res["decision_source"] == "Consensus"


def test_validation_both_non_compliant(db_session: Session, monkeypatch):
    """Case 2: Both engines find the product NON_COMPLIANT."""
    monkeypatch.setenv("AI_ENABLED", "True")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=50.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    mock_ai_eval = [{"rule_code": "LM-001", "status": "FAIL", "message": "Missing MRP"}]
    with patch("app.services.ai_service.AIService.evaluate_compliance", return_value=mock_ai_eval):
        res = validate_ai_vs_deterministic(db_session, verification.id)

    assert res["deterministic_result"] == "NON_COMPLIANT"
    assert res["ai_result"] == "NON_COMPLIANT"
    assert res["agreement"] is True
    assert res["final_result"] == "NON_COMPLIANT"
    assert res["review_required"] is False
    assert res["decision_source"] == "Consensus"


def test_validation_deterministic_compliant_ai_non_compliant(db_session: Session, monkeypatch):
    """Case 3: Deterministic is COMPLIANT, but AI claims NON_COMPLIANT (Deterministic wins)."""
    monkeypatch.setenv("AI_ENABLED", "True")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    _add_compliant_fields(db_session, verification.id)

    mock_ai_eval = [{"rule_code": "LM-001", "status": "WARNING", "message": "Suspect alignment"}]
    with patch("app.services.ai_service.AIService.evaluate_compliance", return_value=mock_ai_eval):
        res = validate_ai_vs_deterministic(db_session, verification.id)

    assert res["deterministic_result"] == "COMPLIANT"
    assert res["ai_result"] == "NON_COMPLIANT"
    assert res["agreement"] is False
    assert res["final_result"] == "COMPLIANT"
    assert res["review_required"] is True
    assert res["decision_source"] == "Deterministic Engine (Authoritative)"


def test_validation_deterministic_non_compliant_ai_compliant(db_session: Session, monkeypatch):
    """Case 4: Deterministic is NON_COMPLIANT, but AI claims COMPLIANT (Deterministic wins)."""
    monkeypatch.setenv("AI_ENABLED", "True")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=50.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    with patch("app.services.ai_service.AIService.evaluate_compliance", return_value=[]):
        res = validate_ai_vs_deterministic(db_session, verification.id)

    assert res["deterministic_result"] == "NON_COMPLIANT"
    assert res["ai_result"] == "COMPLIANT"
    assert res["agreement"] is False
    assert res["final_result"] == "NON_COMPLIANT"
    assert res["review_required"] is True
    assert res["decision_source"] == "Deterministic Engine (Authoritative)"


def test_api_compliance_validate_endpoint(client, db_session: Session, monkeypatch):
    """Test the GET /api/verifications/{id}/compliance/validate endpoint."""
    monkeypatch.setenv("AI_ENABLED", "True")
    get_settings.cache_clear()

    verification = Verification(
        status=VerificationStatus.COMPLETED,
        overall_score=100.0,
        source_image_path="test.jpg"
    )
    db_session.add(verification)
    db_session.commit()

    _add_compliant_fields(db_session, verification.id)

    with patch("app.services.ai_service.AIService.evaluate_compliance", return_value=[]):
        response = client.get(f"/api/verifications/{verification.id}/compliance/validate")

    assert response.status_code == 200
    data = response.json()
    assert data["verification_id"] == str(verification.id)
    assert data["deterministic_result"] == "COMPLIANT"
    assert data["ai_result"] == "COMPLIANT"
    assert data["agreement"] is True
    assert data["final_result"] == "COMPLIANT"
    assert data["review_required"] is False
    assert data["decision_source"] == "Consensus"
