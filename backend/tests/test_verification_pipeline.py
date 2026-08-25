import io
import os
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, VerificationStatus
from app.models.user import User
from app.models.verification import Verification
from app.services import image_service, ocr_service, verification_pipeline_service
from app.utils.exceptions import BadRequestException, NotFoundException
from app.utils.security import create_access_token, hash_password


def create_dummy_image_file() -> str:
    """Helper to save a valid test image to disk."""
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 100), color="white")
    img.save(buf, format="JPEG")
    return image_service.save_image_file(buf.getvalue(), "pipeline_test.jpg")


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
def inspector_user(db_session: Session) -> User:
    """Create inspector user."""
    user = User(
        name="Inspector Pipeline",
        email="pipeline.inspector@metrology.gov",
        password_hash=hash_password("InspectorPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(inspector_user: User) -> dict:
    """Generate Bearer Authorization header."""
    token = create_access_token(user_id=inspector_user.id, role=inspector_user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. VERIFICATION PIPELINE SERVICE TESTS
# ----------------------------------------------------------------------

def test_pipeline_service_successful_run(db_session: Session, inspector_user: User, monkeypatch):
    """Test full pipeline service execution: image -> OCR -> fields -> completed."""
    image_path = create_dummy_image_file()
    try:
        # Create verification record
        verification = Verification(
            source_image_path=image_path,
            inspector_id=inspector_user.id,
            status=VerificationStatus.PENDING,
        )
        db_session.add(verification)
        db_session.commit()
        db_session.refresh(verification)

        # Mock OCR output
        mock_ocr = "M.R.P.: Rs. 350.00\nNET WT: 250 g\nBATCH NO: B-998\nCOUNTRY OF ORIGIN: India"
        monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: mock_ocr)

        # Process verification
        processed = verification_pipeline_service.process_verification(db_session, verification.id)

        assert processed.status == VerificationStatus.COMPLETED
        assert processed.ocr_raw_text == mock_ocr
        assert processed.completed_at is not None

        # Check extracted fields
        fields = verification_pipeline_service.get_verification_fields(db_session, verification.id)
        assert len(fields) >= 4
        field_names = {f.field_name for f in fields}
        assert "mrp" in field_names
        assert "net_quantity" in field_names
        assert "batch_number" in field_names
        assert "country_of_origin" in field_names
    finally:
        image_service.delete_image_file(image_path)


def test_pipeline_service_idempotence(db_session: Session, inspector_user: User, monkeypatch):
    """Ensure running the pipeline multiple times does not produce duplicate fields."""
    image_path = create_dummy_image_file()
    try:
        verification = Verification(
            source_image_path=image_path,
            inspector_id=inspector_user.id,
            status=VerificationStatus.PENDING,
        )
        db_session.add(verification)
        db_session.commit()

        mock_ocr = "MRP: Rs. 100.00\nNET QTY: 1 kg"
        monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: mock_ocr)

        # Process twice
        verification_pipeline_service.process_verification(db_session, verification.id)
        fields_first = verification_pipeline_service.get_verification_fields(db_session, verification.id)

        verification_pipeline_service.process_verification(db_session, verification.id)
        fields_second = verification_pipeline_service.get_verification_fields(db_session, verification.id)

        assert len(fields_first) == len(fields_second)
    finally:
        image_service.delete_image_file(image_path)


def test_pipeline_service_missing_verification_or_image(db_session: Session):
    """Ensure pipeline raises appropriate exceptions on missing entity or file."""
    with pytest.raises(NotFoundException):
        verification_pipeline_service.process_verification(db_session, uuid.uuid4())

    # Verification with missing image file on disk
    v = Verification(source_image_path="nonexistent/file.jpg", status=VerificationStatus.PENDING)
    db_session.add(v)
    db_session.commit()

    with pytest.raises(BadRequestException):
        verification_pipeline_service.process_verification(db_session, v.id)


def test_pipeline_service_handles_ocr_error(db_session: Session, inspector_user: User, monkeypatch):
    """Ensure OCR error sets verification status to FAILED."""
    image_path = create_dummy_image_file()
    try:
        verification = Verification(
            source_image_path=image_path,
            inspector_id=inspector_user.id,
            status=VerificationStatus.PENDING,
        )
        db_session.add(verification)
        db_session.commit()

        def mock_error(*args, **kwargs):
            raise RuntimeError("OCR Engine crashed")

        monkeypatch.setattr(ocr_service, "extract_text_from_image", mock_error)

        with pytest.raises(Exception):
            verification_pipeline_service.process_verification(db_session, verification.id)

        # Reload verification from database
        db_session.expire_all()
        updated_v = db_session.get(Verification, verification.id)
        assert updated_v.status == VerificationStatus.FAILED
    finally:
        image_service.delete_image_file(image_path)


# ----------------------------------------------------------------------
# 2. API ENDPOINTS INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_api_process_verification_endpoint(client: TestClient, auth_headers: dict, monkeypatch):
    """Test POST /api/verifications/{id}/process endpoint."""
    mock_ocr = "M.R.P.: Rs. 499.00\nNET WEIGHT: 500 g\nBATCH: BX-102"
    monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: mock_ocr)

    # Upload image first
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="white").save(buf, format="JPEG")
    up_res = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", buf.getvalue(), "image/jpeg")},
        headers=auth_headers,
    )
    assert up_res.status_code == 201
    v_id = up_res.json()["id"]

    # Call process endpoint
    proc_res = client.post(f"/api/verifications/{v_id}/process", headers=auth_headers)
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["status"] == "completed"
    assert proc_data["ocr_raw_text"] == mock_ocr

    # Call fields endpoint
    fields_res = client.get(f"/api/verifications/{v_id}/fields", headers=auth_headers)
    assert fields_res.status_code == 200
    fields_data = fields_res.json()
    assert len(fields_data) >= 3

    # Check unauthorized requests
    assert client.post(f"/api/verifications/{v_id}/process").status_code == 401
    assert client.get(f"/api/verifications/{v_id}/fields").status_code == 401

    # Check non-existent verification ID
    assert client.post(f"/api/verifications/{uuid.uuid4()}/process", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{uuid.uuid4()}/fields", headers=auth_headers).status_code == 404
