import io
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, UserRole, VerificationStatus
from app.models.user import User
from app.models.verification import Verification
from app.services import audit_service, image_service, ocr_service
from app.utils.exceptions import NotFoundException
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
def inspector_user(db_session: Session) -> User:
    """Create inspector user."""
    user = User(
        name="Audit Inspector",
        email="audit.inspector@metrology.gov",
        password_hash=hash_password("AuditInspectorPass123!"),
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
# 1. AUDIT SERVICE TESTS
# ----------------------------------------------------------------------

def test_create_and_retrieve_audit_logs(db_session: Session, inspector_user: User):
    """Test manual creation and retrieval of audit events."""
    v = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/audit_test.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    # Log 2 events
    log1 = audit_service.create_audit_log(
        db=db_session,
        verification_id=v.id,
        user_id=inspector_user.id,
        action=AuditAction.IMAGE_UPLOADED,
        status="SUCCESS",
        details="Initial image upload",
    )
    log2 = audit_service.create_audit_log(
        db=db_session,
        verification_id=v.id,
        user_id=inspector_user.id,
        action=AuditAction.OCR_PROCESSED,
        status="SUCCESS",
        details="OCR scanned",
    )

    logs = audit_service.get_verification_audit_logs(db_session, v.id)
    assert len(logs) == 2
    assert logs[0].action == AuditAction.IMAGE_UPLOADED
    assert logs[1].action == AuditAction.OCR_PROCESSED


def test_audit_logs_cascade_delete(db_session: Session, inspector_user: User):
    """Ensure deleting verification cascades and deletes its audit logs."""
    v = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/cascade.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(v)
    db_session.commit()

    audit_service.create_audit_log(
        db=db_session,
        verification_id=v.id,
        action=AuditAction.IMAGE_UPLOADED,
    )
    assert db_session.query(AuditLog).filter(AuditLog.verification_id == v.id).count() == 1

    # Delete verification
    db_session.delete(v)
    db_session.commit()

    assert db_session.query(AuditLog).filter(AuditLog.verification_id == v.id).count() == 0


def test_get_audit_logs_nonexistent_verification(db_session: Session):
    """Ensure retrieving audit logs for nonexistent verification raises NotFoundException."""
    with pytest.raises(NotFoundException):
        audit_service.get_verification_audit_logs(db_session, uuid.uuid4())


# ----------------------------------------------------------------------
# 2. PIPELINE AUDIT TRAIL INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_full_pipeline_records_audit_trail(client: TestClient, auth_headers: dict, monkeypatch):
    """Test that executing pipeline stages records corresponding audit events."""
    mock_ocr = "M.R.P.: Rs. 350.00\nNET WEIGHT: 250 g\nBATCH: B-101\nCOUNTRY OF ORIGIN: India\nMFD BY: Nestle India Ltd"
    monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: mock_ocr)

    # 1. Upload image -> IMAGE_UPLOADED
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="white").save(buf, format="JPEG")
    up_res = client.post(
        "/api/verifications/upload",
        files={"file": ("product.jpg", buf.getvalue(), "image/jpeg")},
        headers=auth_headers,
    )
    assert up_res.status_code == 201
    v_id = up_res.json()["id"]

    # 2. Process OCR & extraction -> OCR_PROCESSED, FIELDS_EXTRACTED
    proc_res = client.post(f"/api/verifications/{v_id}/process", headers=auth_headers)
    assert proc_res.status_code == 200

    # 3. Evaluate compliance -> COMPLIANCE_CHECKED
    comp_res = client.post(f"/api/verifications/{v_id}/compliance", headers=auth_headers)
    assert comp_res.status_code == 200

    # 4. Generate report -> REPORT_GENERATED
    rep_res = client.post(f"/api/verifications/{v_id}/report", headers=auth_headers)
    assert rep_res.status_code == 200

    # 5. Retrieve audit trail (GET)
    audit_res = client.get(f"/api/verifications/{v_id}/audit-logs", headers=auth_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()

    assert len(logs) >= 5
    actions = [log["action"] for log in logs]
    assert "IMAGE_UPLOADED" in actions
    assert "OCR_PROCESSED" in actions
    assert "FIELDS_EXTRACTED" in actions
    assert "COMPLIANCE_CHECKED" in actions
    assert "REPORT_GENERATED" in actions

    # Unauthorized & 404 checks
    assert client.get(f"/api/verifications/{v_id}/audit-logs").status_code == 401
    assert client.get(f"/api/verifications/{uuid.uuid4()}/audit-logs", headers=auth_headers).status_code == 404
