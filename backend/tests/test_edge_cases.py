import io
import uuid
from datetime import timedelta
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
from app.services import ocr_service
from app.utils.security import create_access_token, hash_password


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
def inspector(db_session: Session) -> User:
    user = User(
        name="Edge Case Inspector",
        email="edge.inspector@metrology.gov.in",
        password_hash=hash_password("EdgePass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(inspector: User) -> dict:
    token = create_access_token(user_id=inspector.id, role=inspector.role.value)
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. ROUTING & UUID VALIDATION EDGE CASES
# ----------------------------------------------------------------------

def test_invalid_uuid_format_returns_422(client: TestClient, auth_headers: dict):
    """Verify invalid UUID string in URL returns HTTP 422."""
    assert client.get("/api/verifications/invalid-uuid-string", headers=auth_headers).status_code == 422
    assert client.post("/api/verifications/not-a-uuid/process", headers=auth_headers).status_code == 422
    assert client.get("/api/verifications/12345/report/pdf", headers=auth_headers).status_code == 422


def test_missing_verification_returns_404(client: TestClient, auth_headers: dict):
    """Verify non-existent verification UUID returns HTTP 404."""
    random_id = uuid.uuid4()
    assert client.get(f"/api/verifications/{random_id}", headers=auth_headers).status_code == 404
    assert client.post(f"/api/verifications/{random_id}/process", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{random_id}/fields", headers=auth_headers).status_code == 404
    assert client.post(f"/api/verifications/{random_id}/compliance", headers=auth_headers).status_code == 404
    assert client.post(f"/api/verifications/{random_id}/report", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{random_id}/report/pdf", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{random_id}/audit-logs", headers=auth_headers).status_code == 404


# ----------------------------------------------------------------------
# 2. IMAGE & OCR PROCESSING EDGE CASES
# ----------------------------------------------------------------------

def test_missing_image_file_on_disk_returns_400(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    inspector: User,
):
    """Verify processing verification whose image was deleted from disk returns 400."""
    v = Verification(
        inspector_id=inspector.id,
        source_image_path="uploads/images/nonexistent_image_on_disk.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    res = client.post(f"/api/verifications/{v.id}/process", headers=auth_headers)
    assert res.status_code == 400
    assert "not found on disk" in res.json()["error"]["message"].lower()


def test_empty_ocr_result_handles_gracefully(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    inspector: User,
    monkeypatch,
):
    """Verify blank OCR text is processed without errors resulting in 0 fields and low compliance score."""
    monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: "")

    # 1. Upload valid image
    buf = io.BytesIO()
    Image.new("RGB", (50, 50), color="white").save(buf, format="JPEG")
    up_res = client.post(
        "/api/verifications/upload",
        files={"file": ("blank_label.jpg", buf.getvalue(), "image/jpeg")},
        headers=auth_headers,
    )
    v_id = up_res.json()["id"]

    # 2. Process
    proc_res = client.post(f"/api/verifications/{v_id}/process", headers=auth_headers)
    assert proc_res.status_code == 200

    # 3. Fields should be empty
    fields_res = client.get(f"/api/verifications/{v_id}/fields", headers=auth_headers)
    assert fields_res.status_code == 200
    assert len(fields_res.json()) == 0

    # 4. Compliance evaluation works and identifies all missing fields
    comp_res = client.post(f"/api/verifications/{v_id}/compliance", headers=auth_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["failed_rules"] > 0
    assert comp_res.json()["overall_score"] < 50.0


# ----------------------------------------------------------------------
# 3. REPORT & PDF DEPENDENCY ORDER EDGE CASES
# ----------------------------------------------------------------------

def test_report_generation_before_compliance_evaluation_returns_400(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    inspector: User,
):
    """Verify attempting report generation before running compliance rules returns HTTP 400."""
    v = Verification(
        inspector_id=inspector.id,
        source_image_path="uploads/images/pending_eval.jpg",
        status=VerificationStatus.PROCESSING,
    )
    db_session.add(v)
    db_session.commit()

    res = client.post(f"/api/verifications/{v.id}/report", headers=auth_headers)
    assert res.status_code == 400
    assert "must be completed" in res.json()["error"]["message"].lower()


def test_pdf_export_without_report_returns_404(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    inspector: User,
):
    """Verify attempting PDF export when report does not exist returns HTTP 404."""
    v = Verification(
        inspector_id=inspector.id,
        source_image_path="uploads/images/unreported.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    res = client.get(f"/api/verifications/{v.id}/report/pdf", headers=auth_headers)
    assert res.status_code == 404
