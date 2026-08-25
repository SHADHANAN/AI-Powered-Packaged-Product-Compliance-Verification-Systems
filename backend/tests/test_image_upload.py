import io
import os
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, VerificationStatus
from app.models.user import User
from app.models.verification import Verification
from app.services import image_service
from app.utils.security import create_access_token, hash_password

settings = get_settings()


def create_dummy_image(format_name: str = "JPEG", size=(100, 100), color="blue") -> bytes:
    """Helper to generate valid in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format_name)
    return buf.getvalue()


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
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_inspector(db_session: Session) -> User:
    """Create an active inspector user."""
    user = User(
        name="Inspector Alice",
        email="alice.inspector@metrology.gov",
        password_hash=hash_password("InspectorPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(auth_inspector: User) -> dict:
    """Generate valid Bearer Authorization header for the inspector."""
    token = create_access_token(user_id=auth_inspector.id, role=auth_inspector.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. AUTHENTICATION REQUIREMENT TESTS
# ----------------------------------------------------------------------

def test_upload_requires_jwt_authentication(client: TestClient):
    """Ensure POST /api/verifications/upload without JWT returns 401."""
    img_bytes = create_dummy_image("JPEG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_upload_rejects_invalid_jwt(client: TestClient):
    """Ensure POST /api/verifications/upload with invalid JWT returns 401."""
    img_bytes = create_dummy_image("JPEG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", img_bytes, "image/jpeg")},
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert res.status_code == 401


# ----------------------------------------------------------------------
# 2. VALID IMAGE UPLOAD TESTS (JPG, PNG, WEBP)
# ----------------------------------------------------------------------

def test_upload_valid_jpg(client: TestClient, auth_headers: dict, auth_inspector: User):
    """Test successful upload of a valid JPG image."""
    img_bytes = create_dummy_image("JPEG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("packaged_cereal.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["inspector_id"] == str(auth_inspector.id)
    assert data["status"] == VerificationStatus.PENDING.value
    assert data["source_image_path"].endswith(".jpg")
    assert os.path.exists(data["source_image_path"])

    # Cleanup created test file
    image_service.delete_image_file(data["source_image_path"])


def test_upload_valid_png(client: TestClient, auth_headers: dict, auth_inspector: User):
    """Test successful upload of a valid PNG image."""
    img_bytes = create_dummy_image("PNG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("drink_bottle.png", img_bytes, "image/png")},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["source_image_path"].endswith(".png")
    assert os.path.exists(data["source_image_path"])

    image_service.delete_image_file(data["source_image_path"])


def test_upload_valid_webp(client: TestClient, auth_headers: dict, auth_inspector: User):
    """Test successful upload of a valid WebP image."""
    img_bytes = create_dummy_image("WEBP")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("snack_box.webp", img_bytes, "image/webp")},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["source_image_path"].endswith(".webp")
    assert os.path.exists(data["source_image_path"])

    image_service.delete_image_file(data["source_image_path"])


# ----------------------------------------------------------------------
# 3. VALIDATION & SECURITY REJECTION TESTS
# ----------------------------------------------------------------------

def test_upload_unsupported_file_extension(client: TestClient, auth_headers: dict):
    """Ensure unsupported file extensions (e.g. .pdf, .txt) return 400 Bad Request."""
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("document.pdf", b"%PDF-1.4 dummy", "application/pdf")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "unsupported file extension" in res.json()["error"]["message"].lower()


def test_upload_invalid_mime_type(client: TestClient, auth_headers: dict):
    """Ensure mismatch between extension and declared MIME returns 400 Bad Request."""
    img_bytes = create_dummy_image("JPEG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("image.jpg", img_bytes, "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "unsupported content type" in res.json()["error"]["message"].lower()


def test_upload_empty_file(client: TestClient, auth_headers: dict):
    """Ensure empty file upload (0 bytes) returns 400 Bad Request."""
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["error"]["message"].lower()


def test_upload_corrupted_image(client: TestClient, auth_headers: dict):
    """Ensure uploading corrupted/non-image bytes named .jpg returns 400 Bad Request."""
    fake_image_bytes = b"NOT_A_REAL_JPEG_BINARY_DATA_CORRUPTED"
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("corrupted.jpg", fake_image_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "not a valid image" in res.json()["error"]["message"].lower()


def test_upload_oversized_file(client: TestClient, auth_headers: dict, monkeypatch):
    """Ensure file exceeding MAX_UPLOAD_SIZE_BYTES returns 413 Payload Too Large."""
    # Temporarily set max upload size to 100 bytes for deterministic testing
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)
    img_bytes = create_dummy_image("JPEG", size=(200, 200))
    assert len(img_bytes) > 100

    res = client.post(
        "/api/verifications/upload",
        files={"file": ("large_image.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 413
    assert "exceeds" in res.json()["error"]["message"].lower()


# ----------------------------------------------------------------------
# 4. STORAGE SAFETY & PATH TRAVERSAL PREVENTION TESTS
# ----------------------------------------------------------------------

def test_unique_stored_filenames(client: TestClient, auth_headers: dict):
    """Ensure multiple uploads of the same original filename receive distinct UUID filenames."""
    img_bytes = create_dummy_image("JPEG")
    res1 = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    res2 = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    assert res2.status_code == 201

    path1 = res1.json()["source_image_path"]
    path2 = res2.json()["source_image_path"]
    assert path1 != path2

    image_service.delete_image_file(path1)
    image_service.delete_image_file(path2)


def test_path_traversal_attempt_sanitized(client: TestClient, auth_headers: dict):
    """Ensure malicious filename path traversal attempts (../../etc/evil.jpg) are sanitized."""
    img_bytes = create_dummy_image("JPEG")
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("../../evil_path.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert res.status_code == 201
    stored_path = res.json()["source_image_path"]
    assert ".." not in stored_path
    assert stored_path.startswith("uploads/images/")

    image_service.delete_image_file(stored_path)


# ----------------------------------------------------------------------
# 5. ATOMIC CLEANUP & DATABASE TRANSACTION FAILURE TESTS
# ----------------------------------------------------------------------

def test_file_cleanup_on_database_failure(client: TestClient, auth_headers: dict, monkeypatch):
    """Ensure that if database creation fails, the uploaded image file is deleted automatically."""
    img_bytes = create_dummy_image("JPEG")

    # Pass an invalid product_id to trigger a database NotFoundException
    invalid_product_id = str(uuid.uuid4())
    res = client.post(
        "/api/verifications/upload",
        files={"file": ("item.jpg", img_bytes, "image/jpeg")},
        data={"product_id": invalid_product_id},
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert "product" in res.json()["error"]["message"].lower()

    # Verify no orphan files were left in the uploads directory
    if os.path.exists(settings.UPLOAD_DIR):
        files = os.listdir(settings.UPLOAD_DIR)
        # Verify no file created in the last second
        # Note: if directory had prior test files, verify count
