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
from app.models.compliance_check import ComplianceCheck
from app.models.enums import AuditAction, ComplianceStatus, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.models.verification import Verification
from app.services import ocr_service
from app.utils.security import hash_password


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
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_inspector(db_session: Session) -> User:
    """Create registered inspector user in database."""
    user = User(
        name="Lead Inspector Verma",
        email="verma.inspector@metrology.gov.in",
        password_hash=hash_password("VermaSecurePass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_complete_end_to_end_verification_lifecycle(
    client: TestClient,
    registered_inspector: User,
    db_session: Session,
    monkeypatch,
):
    """Test full 10-step end-to-end verification pipeline lifecycle."""
    # Mock OCR extraction to return deterministic Legal Metrology label text
    mock_ocr_label = (
        "PREMIUM ALMOND COOKIES\n"
        "BRAND: NutriBite\n"
        "NET WEIGHT: 200 g\n"
        "MAXIMUM RETAIL PRICE: Rs. 150.00 (INCL. OF ALL TAXES)\n"
        "BATCH NO: NB-2026-08\n"
        "MFG DATE: 08/2026\n"
        "COUNTRY OF ORIGIN: India\n"
        "MANUFACTURED & PACKED BY: NutriBite Foods Pvt Ltd, Industrial Area, Bangalore 560001\n"
        "CONSUMER CARE: care@nutribite.com, Toll Free: 1800-123-4567\n"
    )
    monkeypatch.setattr(ocr_service, "extract_text_from_image", lambda *args, **kwargs: mock_ocr_label)

    # ------------------------------------------------------------------
    # Step 1: User Login -> JWT Authentication
    # ------------------------------------------------------------------
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "verma.inspector@metrology.gov.in",
            "password": "VermaSecurePass123!",
        },
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    token = token_data["access_token"]
    assert token_data["token_type"] == "bearer"
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Step 1b: Verify profile via /auth/me
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "verma.inspector@metrology.gov.in"
    assert me_res.json()["role"] == "inspector"

    # ------------------------------------------------------------------
    # Step 2: Upload Packaged Product Image
    # ------------------------------------------------------------------
    img_buf = io.BytesIO()
    Image.new("RGB", (200, 200), color="white").save(img_buf, format="JPEG")
    upload_res = client.post(
        "/api/verifications/upload",
        files={"file": ("almond_cookies_label.jpg", img_buf.getvalue(), "image/jpeg")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    v_data = upload_res.json()
    verification_id = v_data["id"]
    assert v_data["status"] == "pending"
    assert v_data["inspector_id"] == str(registered_inspector.id)

    # ------------------------------------------------------------------
    # Step 3: Run OCR & Structured Field Extraction Pipeline
    # ------------------------------------------------------------------
    process_res = client.post(f"/api/verifications/{verification_id}/process", headers=auth_headers)
    assert process_res.status_code == 200
    proc_data = process_res.json()
    assert proc_data["status"] == "completed"
    assert proc_data["ocr_raw_text"] is not None

    # ------------------------------------------------------------------
    # Step 4: Retrieve Extracted Fields
    # ------------------------------------------------------------------
    fields_res = client.get(f"/api/verifications/{verification_id}/fields", headers=auth_headers)
    assert fields_res.status_code == 200
    fields = fields_res.json()
    assert len(fields) >= 5
    field_names = [f["field_name"] for f in fields]
    assert "mrp" in field_names
    assert "net_quantity" in field_names
    assert "batch_number" in field_names
    assert "country_of_origin" in field_names

    # ------------------------------------------------------------------
    # Step 5: Evaluate Legal Metrology Compliance Rules
    # ------------------------------------------------------------------
    comp_eval_res = client.post(f"/api/verifications/{verification_id}/compliance", headers=auth_headers)
    assert comp_eval_res.status_code == 200
    comp_data = comp_eval_res.json()
    assert comp_data["overall_score"] > 80.0
    assert comp_data["total_rules"] == 12
    assert comp_data["passed_rules"] >= 8

    # ------------------------------------------------------------------
    # Step 6: Retrieve Compliance Evaluation Summary
    # ------------------------------------------------------------------
    comp_get_res = client.get(f"/api/verifications/{verification_id}/compliance", headers=auth_headers)
    assert comp_get_res.status_code == 200
    assert comp_get_res.json()["overall_score"] == comp_data["overall_score"]

    # ------------------------------------------------------------------
    # Step 7: Generate Structured Compliance Report
    # ------------------------------------------------------------------
    report_gen_res = client.post(f"/api/verifications/{verification_id}/report", headers=auth_headers)
    assert report_gen_res.status_code == 200
    rep_data = report_gen_res.json()
    assert rep_data["verification_id"] == verification_id
    assert rep_data["summary"]["total_rules"] == 12
    assert rep_data["inspector"]["email"] == registered_inspector.email

    # ------------------------------------------------------------------
    # Step 8: Retrieve Latest Compliance Report
    # ------------------------------------------------------------------
    report_get_res = client.get(f"/api/verifications/{verification_id}/report", headers=auth_headers)
    assert report_get_res.status_code == 200
    assert report_get_res.json()["report_id"] == rep_data["report_id"]

    # ------------------------------------------------------------------
    # Step 9: Export PDF Compliance Report
    # ------------------------------------------------------------------
    pdf_res = client.get(f"/api/verifications/{verification_id}/report/pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert f'filename="compliance_report_{verification_id}.pdf"' in pdf_res.headers["content-disposition"]
    assert pdf_res.content.startswith(b"%PDF")
    assert len(pdf_res.content) > 1000

    # ------------------------------------------------------------------
    # Step 10: Retrieve Chronological Audit Trail
    # ------------------------------------------------------------------
    audit_res = client.get(f"/api/verifications/{verification_id}/audit-logs", headers=auth_headers)
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 6
    actions = [a["action"] for a in audit_logs]
    assert actions == [
        "IMAGE_UPLOADED",
        "OCR_PROCESSED",
        "FIELDS_EXTRACTED",
        "COMPLIANCE_CHECKED",
        "REPORT_GENERATED",
        "REPORT_PDF_EXPORTED",
    ]


def test_failure_isolation_and_rollback(client: TestClient, registered_inspector: User, monkeypatch):
    """Ensure failures in pipeline stages do not corrupt previous state."""
    # 1. Upload valid image
    token = client.post(
        "/api/auth/login",
        json={"email": "verma.inspector@metrology.gov.in", "password": "VermaSecurePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="white").save(img_buf, format="JPEG")
    up_res = client.post(
        "/api/verifications/upload",
        files={"file": ("fail_test.jpg", img_buf.getvalue(), "image/jpeg")},
        headers=headers,
    )
    v_id = up_res.json()["id"]

    # 2. Simulate OCR failure during processing
    def failing_ocr(*args, **kwargs):
        raise RuntimeError("Simulated OCR engine failure")

    monkeypatch.setattr(ocr_service, "extract_text_from_image", failing_ocr)

    proc_res = client.post(f"/api/verifications/{v_id}/process", headers=headers)
    assert proc_res.status_code == 500

    # Verification status is marked as failed cleanly
    v_check = client.get(f"/api/verifications/{v_id}", headers=headers)
    assert v_check.status_code == 200
    assert v_check.json()["status"] == "failed"

    # 3. Report generation fails cleanly before compliance
    rep_res = client.post(f"/api/verifications/{v_id}/report", headers=headers)
    assert rep_res.status_code == 400
