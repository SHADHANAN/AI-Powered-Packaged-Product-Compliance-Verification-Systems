import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate
from app.services import user_service
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for auth tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
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
def test_user(db_session: Session) -> User:
    """Create an active inspector user for testing authentication."""
    user_in = UserCreate(
        name="Auth Test User",
        email="auth_user@metrology.gov",
        password="ValidPassword123!",
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    return user_service.create_user(db_session, user_in)


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    """Create an inactive user for testing authentication failures."""
    user = User(
        name="Inactive Officer",
        email="inactive@metrology.gov",
        password_hash=hash_password("InactivePass123!"),
        role=UserRole.INSPECTOR,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_success(client: TestClient, test_user: User):
    """Test successful user login returns HTTP 200."""
    res = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_returns_bearer_token(client: TestClient, test_user: User):
    """Test login response contains valid JWT bearer token that decodes correctly."""
    res = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(test_user.id)


def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with wrong password returns HTTP 401."""
    res = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "IncorrectPassword999"},
    )
    assert res.status_code == 401
    assert res.json()["success"] is False
    assert "incorrect email or password" in res.json()["error"]["message"].lower()


def test_login_unknown_email(client: TestClient):
    """Test login with non-existent email returns HTTP 401."""
    res = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@metrology.gov", "password": "AnyPassword123"},
    )
    assert res.status_code == 401
    assert res.json()["success"] is False
    assert "incorrect email or password" in res.json()["error"]["message"].lower()


def test_login_inactive_user(client: TestClient, inactive_user: User):
    """Test login for inactive user account returns HTTP 401."""
    res = client.post(
        "/api/auth/login",
        json={"email": inactive_user.email, "password": "InactivePass123!"},
    )
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_login_invalid_request(client: TestClient):
    """Test login with invalid payload (e.g. bad email format) returns HTTP 422."""
    res = client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": ""},
    )
    assert res.status_code == 422


def test_jwt_contains_subject(test_user: User):
    """Test that generated JWT payload contains subject claim matching user ID."""
    token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(test_user.id)


def test_jwt_contains_expiration(test_user: User):
    """Test that generated JWT payload contains valid future expiration timestamp."""
    token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_jwt_contains_role(test_user: User):
    """Test that generated JWT payload contains role claim."""
    token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["role"] == test_user.role.value


def test_invalid_jwt():
    """Test decoding an invalid/garbage JWT safely returns None."""
    assert decode_access_token("not.a.valid.jwt.token") is None
    assert decode_access_token("") is None


def test_expired_jwt(test_user: User):
    """Test that an expired JWT is rejected by decode_access_token."""
    expired_token = create_access_token(
        user_id=test_user.id,
        role=test_user.role.value,
        expires_delta=timedelta(seconds=-10),  # expired in the past
    )
    assert decode_access_token(expired_token) is None


def test_missing_bearer_token(client: TestClient):
    """Test GET /api/auth/me without Authorization header returns HTTP 401."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_malformed_bearer_token(client: TestClient):
    """Test GET /api/auth/me with malformed Authorization header returns HTTP 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_auth_me_success(client: TestClient, test_user: User):
    """Test GET /api/auth/me with valid Bearer token returns user profile."""
    token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["id"] == str(test_user.id)
    assert user_data["email"] == test_user.email
    assert user_data["role"] == test_user.role.value


def test_auth_me_invalid_token(client: TestClient):
    """Test GET /api/auth/me with an invalid JWT token returns HTTP 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer eyJhbGciOi.fake.jwt"})
    assert res.status_code == 401


def test_auth_me_inactive_user(client: TestClient, inactive_user: User):
    """Test GET /api/auth/me with token for inactive user returns HTTP 401."""
    token = create_access_token(user_id=inactive_user.id, role=inactive_user.role.value)
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_auth_me_does_not_expose_password_hash(client: TestClient, test_user: User):
    """Test GET /api/auth/me response does not expose password or password_hash."""
    token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert "password" not in user_data
    assert "password_hash" not in user_data
