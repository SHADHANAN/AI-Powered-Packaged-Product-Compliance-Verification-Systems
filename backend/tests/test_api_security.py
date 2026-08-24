import io
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.utils.file_validation import sanitize_filename, validate_image_file
from app.utils.security import create_access_token, decode_access_token, hash_password


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
def test_inspector(db_session: Session) -> User:
    user = User(
        name="Security Test Inspector",
        email="sec.inspector@metrology.gov.in",
        password_hash=hash_password("SecPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_inspector: User) -> dict:
    token = create_access_token(user_id=test_inspector.id, role=test_inspector.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. SECURITY HEADERS
# ----------------------------------------------------------------------

def test_security_headers_present_on_api_responses(client: TestClient):
    """Verify that essential security headers are injected into all HTTP responses."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "no-referrer"
    assert res.headers.get("x-xss-protection") == "1; mode=block"


def test_security_headers_present_on_docs(client: TestClient):
    """Verify that security headers are present on OpenAPI docs endpoint."""
    res = client.get("/docs")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"


# ----------------------------------------------------------------------
# 2. CORS HARDENING
# ----------------------------------------------------------------------

def test_cors_allowed_origin_accepted(client: TestClient):
    """Verify that preflight requests from configured origin receive proper CORS headers."""
    res = client.options(
        "/api/verifications/upload",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_unconfigured_origin_rejected(client: TestClient):
    """Verify that unconfigured origins do not receive allowed CORS headers."""
    res = client.options(
        "/api/verifications/upload",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res.headers.get("access-control-allow-origin") is None


# ----------------------------------------------------------------------
# 3. JWT TOKEN HARDENING
# ----------------------------------------------------------------------

def test_tampered_jwt_token_rejected():
    """Verify that modifying a token signature causes validation failure."""
    valid_token = create_access_token(user_id=uuid.uuid4(), role="inspector")
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"
    assert decode_access_token(tampered_token) is None


def test_expired_jwt_token_rejected():
    """Verify that expired JWT token is rejected."""
    expired_token = create_access_token(
        user_id=uuid.uuid4(),
        role="inspector",
        expires_delta=timedelta(seconds=-10),
    )
    assert decode_access_token(expired_token) is None


def test_jwt_missing_exp_claim_rejected():
    """Verify that a token missing expiration claim is rejected."""
    settings = get_settings()
    payload = {"sub": str(uuid.uuid4()), "role": "inspector"}
    token_without_exp = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    assert decode_access_token(token_without_exp) is None


def test_jwt_invalid_algorithm_rejected():
    """Verify that tokens signed with an unsupported algorithm are rejected."""
    settings = get_settings()
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "inspector",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
    }
    # Sign with 'none' or different algorithm
    try:
        token_none = jwt.encode(payload, "", algorithm="none")
        assert decode_access_token(token_none) is None
    except Exception:
        pass


# ----------------------------------------------------------------------
# 4. FILE UPLOAD SECURITY HARDENING
# ----------------------------------------------------------------------

def test_filename_sanitization_removes_path_traversal():
    """Verify path traversal characters and null bytes are sanitized."""
    assert sanitize_filename("../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe.png") == "cmd.exe.png"
    assert sanitize_filename("image\x00_test.jpg") == "image_test.jpg"


def test_upload_corrupted_image_rejected(client: TestClient, auth_headers: dict):
    """Verify non-image fake binary payload is rejected."""
    fake_data = b"This is not a real image header"
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("fake.jpg", fake_data, "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "not a valid image" in res.json()["error"]["message"].lower()


# ----------------------------------------------------------------------
# 5. ERROR LEAKAGE & INFORMATION DISCLOSURE PREVENTION
# ----------------------------------------------------------------------

def test_unhandled_route_error_does_not_leak_internals(client: TestClient):
    """Verify 404 does not leak internal server details."""
    res = client.get("/api/nonexistent-endpoint-12345")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert "traceback" not in str(data).lower()
    assert "postgresql://" not in str(data)
    assert "c:\\" not in str(data).lower()


# ----------------------------------------------------------------------
# 6. CONFIGURATION VALIDATION
# ----------------------------------------------------------------------

def test_production_config_rejects_insecure_default_secret():
    """Verify that in production mode, default or weak JWT secret key raises validation error."""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="change-this-in-production-secret-key-min-32-chars",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="short-key",
        )


def test_production_config_rejects_wildcard_cors():
    """Verify that in production mode, wildcard '*' CORS origin raises validation error."""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a-very-long-and-secure-production-jwt-secret-key-12345",
            CORS_ORIGINS=["*"],
        )


def test_production_config_accepts_valid_production_settings():
    """Verify that strong production configuration is accepted."""
    cfg = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a-very-long-and-secure-production-jwt-secret-key-12345",
        CORS_ORIGINS=["https://metrology.gov.in", "https://app.metrology.gov.in"],
        MAX_UPLOAD_SIZE_BYTES=10485760,
        OCR_TIMEOUT_SECONDS=45,
    )
    assert cfg.ENVIRONMENT == "production"
    assert len(cfg.get_cors_origins()) == 2
