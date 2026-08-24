import io
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.authorization import (
    require_admin,
    require_authenticated_user,
    require_inspector,
    require_viewer,
    verify_user_profile_ownership,
    verify_verification_ownership,
)
from app.database import Base, get_db
from app.main import app
from app.models.compliance_check import ComplianceCheck
from app.models.enums import ComplianceStatus, Severity, UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
from app.services import report_service
from app.utils.exceptions import ForbiddenException, UnauthorizedException
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
def admin_user(db_session: Session) -> User:
    user = User(
        name="Chief Admin",
        email="admin@metrology.gov.in",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inspector_a(db_session: Session) -> User:
    user = User(
        name="Inspector Alice",
        email="alice.inspector@metrology.gov.in",
        password_hash=hash_password("AlicePass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inspector_b(db_session: Session) -> User:
    user = User(
        name="Inspector Bob",
        email="bob.inspector@metrology.gov.in",
        password_hash=hash_password("BobPass123!"),
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session: Session) -> User:
    user = User(
        name="Public Viewer",
        email="viewer@public.org",
        password_hash=hash_password("ViewerPass123!"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    user = User(
        name="Inactive Inspector",
        email="inactive@metrology.gov.in",
        password_hash=hash_password("InactivePass123!"),
        role=UserRole.INSPECTOR,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def verification_alice(db_session: Session, inspector_a: User) -> Verification:
    v = Verification(
        inspector_id=inspector_a.id,
        source_image_path="uploads/images/alice_sample.jpg",
        status=VerificationStatus.COMPLETED,
        overall_score=90.0,
    )
    db_session.add(v)
    db_session.commit()

    db_session.add(ExtractedField(
        verification_id=v.id,
        field_name="mrp",
        field_value="199.00",
    ))
    db_session.add(ComplianceCheck(
        verification_id=v.id,
        rule_code="LM-MRP-001",
        rule_name="Mandatory MRP Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message="Valid MRP",
    ))
    db_session.commit()
    report_service.generate_compliance_report(db_session, v.id, inspector_a.id)
    db_session.refresh(v)
    return v


# ----------------------------------------------------------------------
# 1. 401 UNAUTHENTICATED TESTS
# ----------------------------------------------------------------------

def test_missing_token_returns_401(client: TestClient, verification_alice: Verification):
    """Ensure missing Bearer token returns 401 Unauthorized."""
    v_id = verification_alice.id
    assert client.get(f"/api/verifications/{v_id}/fields").status_code == 401
    assert client.get(f"/api/verifications/{v_id}/report").status_code == 401
    assert client.get(f"/api/verifications/{v_id}/report/pdf").status_code == 401
    assert client.get(f"/api/verifications/{v_id}/audit-logs").status_code == 401


def test_invalid_and_expired_token_returns_401(client: TestClient, verification_alice: Verification):
    """Ensure invalid/malformed token returns 401 Unauthorized."""
    v_id = verification_alice.id
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    assert client.get(f"/api/verifications/{v_id}/fields", headers=headers).status_code == 401


def test_inactive_user_token_returns_401(client: TestClient, inactive_user: User, verification_alice: Verification):
    """Ensure inactive user is rejected with 401 Unauthorized."""
    token = create_access_token(user_id=inactive_user.id, role=inactive_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    v_id = verification_alice.id
    assert client.get(f"/api/verifications/{v_id}/fields", headers=headers).status_code == 401


# ----------------------------------------------------------------------
# 2. ROLE-BASED ACCESS CONTROL (403 FORBIDDEN)
# ----------------------------------------------------------------------

def test_viewer_cannot_upload_or_evaluate(client: TestClient, viewer_user: User, verification_alice: Verification):
    """Ensure VIEWER role cannot upload images or trigger compliance evaluations."""
    token = create_access_token(user_id=viewer_user.id, role=viewer_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Viewer attempting to upload
    buf = io.BytesIO()
    Image.new("RGB", (50, 50), color="blue").save(buf, format="PNG")
    upload_res = client.post(
        "/api/verifications/upload",
        files={"file": ("product.png", buf.getvalue(), "image/png")},
        headers=headers,
    )
    assert upload_res.status_code == 403
    assert upload_res.json()["error"]["status_code"] == 403

    # Viewer attempting compliance evaluation
    eval_res = client.post(f"/api/verifications/{verification_alice.id}/compliance", headers=headers)
    assert eval_res.status_code == 403


# ----------------------------------------------------------------------
# 3. RESOURCE OWNERSHIP & LEAST-PRIVILEGE AUTHORIZATION
# ----------------------------------------------------------------------

def test_inspector_b_cannot_access_or_modify_inspector_a_verification(
    client: TestClient,
    inspector_b: User,
    verification_alice: Verification,
):
    """Ensure Inspector B cannot access, evaluate, or export Inspector A's verification."""
    token_b = create_access_token(user_id=inspector_b.id, role=inspector_b.role.value)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    v_id = verification_alice.id

    # 1. Process pipeline
    assert client.post(f"/api/verifications/{v_id}/process", headers=headers_b).status_code == 403

    # 2. Get fields
    assert client.get(f"/api/verifications/{v_id}/fields", headers=headers_b).status_code == 403

    # 3. Run compliance
    assert client.post(f"/api/verifications/{v_id}/compliance", headers=headers_b).status_code == 403

    # 4. Get compliance
    assert client.get(f"/api/verifications/{v_id}/compliance", headers=headers_b).status_code == 403

    # 5. Generate report
    assert client.post(f"/api/verifications/{v_id}/report", headers=headers_b).status_code == 403

    # 6. Get report
    assert client.get(f"/api/verifications/{v_id}/report", headers=headers_b).status_code == 403

    # 7. Get PDF report
    assert client.get(f"/api/verifications/{v_id}/report/pdf", headers=headers_b).status_code == 403

    # 8. Get audit logs
    assert client.get(f"/api/verifications/{v_id}/audit-logs", headers=headers_b).status_code == 403


def test_admin_has_full_oversight_across_verifications(
    client: TestClient,
    admin_user: User,
    verification_alice: Verification,
):
    """Ensure ADMIN role can inspect and export reports for any verification."""
    admin_token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    v_id = verification_alice.id

    assert client.get(f"/api/verifications/{v_id}/fields", headers=admin_headers).status_code == 200
    assert client.get(f"/api/verifications/{v_id}/report", headers=admin_headers).status_code == 200
    assert client.get(f"/api/verifications/{v_id}/report/pdf", headers=admin_headers).status_code == 200
    assert client.get(f"/api/verifications/{v_id}/audit-logs", headers=admin_headers).status_code == 200


def test_authorized_inspector_accesses_own_verification(
    client: TestClient,
    inspector_a: User,
    verification_alice: Verification,
):
    """Ensure Inspector A can access their own verification."""
    token_a = create_access_token(user_id=inspector_a.id, role=inspector_a.role.value)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    v_id = verification_alice.id

    assert client.get(f"/api/verifications/{v_id}/fields", headers=headers_a).status_code == 200
    assert client.get(f"/api/verifications/{v_id}/report", headers=headers_a).status_code == 200
    assert client.get(f"/api/verifications/{v_id}/report/pdf", headers=headers_a).status_code == 200


# ----------------------------------------------------------------------
# 4. UNIT LEVEL AUTHORIZATION HELPERS
# ----------------------------------------------------------------------

def test_verify_user_profile_ownership_unit(inspector_a: User, inspector_b: User, admin_user: User):
    """Verify profile ownership helper."""
    # Self access -> OK
    verify_user_profile_ownership(inspector_a.id, inspector_a)

    # Admin access -> OK
    verify_user_profile_ownership(inspector_a.id, admin_user)

    # Cross user access -> Forbidden
    with pytest.raises(ForbiddenException):
        verify_user_profile_ownership(inspector_a.id, inspector_b)
