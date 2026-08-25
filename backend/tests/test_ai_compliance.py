"""Unit tests for the AI integration and fallback layer."""
import uuid
import pytest
from unittest.mock import patch
import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.config import get_settings
from app.models.enums import ComplianceStatus, Severity, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
from app.services import compliance_engine
from app.services.ai_service import AIService, AIServiceException
from app.services.compliance_rules import ALL_RULES
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
        name="Inspector Compliance AI",
        email="compliance.inspector.ai@metrology.gov",
        password_hash=hash_password("InspectorPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_ai_service_mock_provider(monkeypatch):
    """Verify that the mock provider runs successfully and returns parsed JSON results."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    service = AIService()
    fields = {"mrp": "100.0", "net_quantity": "500 g", "quantity_unit": "g"}
    results = service.evaluate_compliance(fields, ALL_RULES)

    assert len(results) == len(ALL_RULES)
    codes = [r["rule_code"] for r in results]
    assert "LM-MRP-001" in codes
    assert "LM-QTY-001" in codes
    assert results[0]["status"] in ["pass", "fail", "warning", "not_applicable", "PASS", "FAIL", "WARNING", "NOT_APPLICABLE"]


def test_ai_service_unsupported_provider(monkeypatch):
    """Verify raising exception when an unsupported AI provider is selected."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "invalid_provider_val")
    get_settings.cache_clear()

    import pydantic
    with pytest.raises(pydantic.ValidationError):
        get_settings()


def test_ai_service_missing_api_key_gemini(monkeypatch):
    """Verify exception raised when API key is missing for live providers (Gemini)."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    get_settings.cache_clear()

    service = AIService()
    with pytest.raises(AIServiceException) as exc_info:
        service.evaluate_compliance({}, ALL_RULES)
    assert "Gemini API key is not configured" in str(exc_info.value)


def test_ai_service_openai_success(monkeypatch):
    """Verify OpenAI provider HTTP parsing is successful and formats correctly."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "fake_openai_key")
    get_settings.cache_clear()

    mock_openai_response = {
        "choices": [
            {
                "message": {
                    "content": """
                    [
                      {
                        "rule_code": "LM-MRP-001",
                        "rule_name": "Mandatory MRP Declaration",
                        "status": "PASS",
                        "severity": "HIGH",
                        "message": "Valid MRP",
                        "expected_value": "Valid MRP",
                        "actual_value": "100.0",
                        "recommendation": null
                      }
                    ]
                    """
                }
            }
        ]
    }

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        return MockResponse(mock_openai_response)

    with patch("httpx.Client.post", side_effect=mock_post):
        service = AIService()
        results = service.evaluate_compliance({}, ALL_RULES)
        assert len(results) == 1
        assert results[0]["rule_code"] == "LM-MRP-001"
        assert results[0]["status"] == "PASS"


def test_ai_service_gemini_success(monkeypatch):
    """Verify Gemini provider HTTP response parsing is successful."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("AI_API_KEY", "fake_gemini_key")
    get_settings.cache_clear()

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """
                            [
                              {
                                "rule_code": "LM-QTY-001",
                                "rule_name": "Mandatory Net Quantity Declaration",
                                "status": "FAIL",
                                "severity": "HIGH",
                                "message": "Missing net quantity",
                                "expected_value": "Valid qty",
                                "actual_value": null,
                                "recommendation": "Add net qty"
                              }
                            ]
                            """
                        }
                    ]
                }
            }
        ]
    }

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        return MockResponse(mock_gemini_response)

    with patch("httpx.Client.post", side_effect=mock_post):
        service = AIService()
        results = service.evaluate_compliance({}, ALL_RULES)
        assert len(results) == 1
        assert results[0]["rule_code"] == "LM-QTY-001"
        assert results[0]["status"] == "FAIL"


def test_evaluate_verification_compliance_ai_success(monkeypatch, db_session: Session, inspector_user: User):
    """Verify that when AI_ENABLED is True and AI succeeds, compliance engine persists results correctly."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

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
        field_value="150.00",
        confidence=0.9,
        source_text="MRP 150.00",
    ))
    db_session.commit()

    summary = compliance_engine.evaluate_verification_compliance(db_session, verification.id, inspector_user.id)

    assert summary.total_rules == len(ALL_RULES)
    assert summary.passed_rules >= 1


def test_evaluate_verification_compliance_ai_failure_fallback(monkeypatch, db_session: Session, inspector_user: User):
    """Verify that if AI service fails, compliance engine falls back to deterministic rules gracefully."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.delenv("AI_API_KEY", raising=False)  # triggers exception in live provider due to key missing
    get_settings.cache_clear()

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
        field_value="150.00",
        confidence=0.9,
        source_text="MRP 150.00",
    ))
    db_session.commit()

    summary = compliance_engine.evaluate_verification_compliance(db_session, verification.id, inspector_user.id)

    assert summary.total_rules == len(ALL_RULES)
    assert summary.passed_rules >= 1


def test_evaluate_verification_compliance_ai_disabled(monkeypatch, db_session: Session, inspector_user: User):
    """Verify that when AI_ENABLED is False, deterministic rules are used directly."""
    monkeypatch.setenv("AI_ENABLED", "False")
    get_settings.cache_clear()

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
        field_value="150.00",
        confidence=0.9,
        source_text="MRP 150.00",
    ))
    db_session.commit()

    summary = compliance_engine.evaluate_verification_compliance(db_session, verification.id, inspector_user.id)

    assert summary.total_rules == len(ALL_RULES)
    assert summary.passed_rules >= 1
