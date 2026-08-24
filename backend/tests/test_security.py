import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole
from app.schemas.user import UserCreate
from app.services import user_service
from app.utils.security import hash_password, verify_password


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for user security testing."""
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
def test_client(db_session: Session):
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_password_hash_is_not_plaintext():
    """Ensure that the hashed password is not equal to plaintext and uses Argon2 format."""
    plaintext = "SecurePassword@123"
    hashed = hash_password(plaintext)
    assert hashed != plaintext
    assert hashed.startswith("$argon2id$")


def test_password_hash_is_different_each_time():
    """Ensure that hashing the same password multiple times produces unique hashes (due to salt)."""
    plaintext = "MySecretPass_2026"
    hash_one = hash_password(plaintext)
    hash_two = hash_password(plaintext)
    assert hash_one != hash_two
    assert verify_password(plaintext, hash_one) is True
    assert verify_password(plaintext, hash_two) is True


def test_verify_correct_password():
    """Ensure verify_password returns True for matching password."""
    password = "CorrectHorseBatteryStaple!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_wrong_password():
    """Ensure verify_password returns False for non-matching password."""
    password = "CorrectPassword123"
    hashed = hash_password(password)
    assert verify_password("WrongPassword456", hashed) is False


def test_invalid_password_hash_handling():
    """Ensure verify_password handles empty, malformed, or garbage hashes gracefully without crashing."""
    assert verify_password("", "$argon2id$somehash") is False
    assert verify_password("password", "") is False
    assert verify_password("password", "invalid_garbage_hash") is False
    assert verify_password("password", "$argon2id$corrupted_payload") is False

    with pytest.raises(ValueError):
        hash_password("")


def test_user_creation_stores_hashed_password(db_session: Session):
    """Ensure user_service.create_user saves an Argon2 hash in the database, never plaintext."""
    plaintext_password = "InspectorSecret#2026"
    user_in = UserCreate(
        name="Officer Alice",
        email="alice@metrology.gov",
        password=plaintext_password,
        role=UserRole.ADMIN,
    )
    user = user_service.create_user(db_session, user_in)
    assert user.id is not None
    assert user.password_hash != plaintext_password
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(plaintext_password, user.password_hash) is True


def test_user_read_does_not_expose_password_hash(test_client: TestClient):
    """Ensure neither API responses nor UserRead schemas expose the password or password_hash."""
    res = test_client.post(
        "/api/users",
        json={
            "name": "Inspector Bob",
            "email": "bob.inspector@metrology.gov",
            "password": "InspectorPassword123",
            "role": "inspector",
        },
    )
    assert res.status_code == 201
    user_data = res.json()
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # Fetch user by ID
    get_res = test_client.get(f"/api/users/{user_data['id']}")
    assert get_res.status_code == 200
    fetched_user = get_res.json()
    assert "password" not in fetched_user
    assert "password_hash" not in fetched_user
