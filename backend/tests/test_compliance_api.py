import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import Verification
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
        name="Compliance Inspector API",
        email="api.inspector@metrology.gov",
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


def test_compliance_api_endpoints_workflow(client: TestClient, db_session: Session, inspector_user: User, auth_headers: dict):
    """Test full compliance API workflow via POST & GET /api/verifications/{id}/compliance."""
    # 1. Create verification
    verification = Verification(
        inspector_id=inspector_user.id,
        source_image_path="uploads/images/sample.jpg",
        status=VerificationStatus.PENDING,
    )
    db_session.add(verification)
    db_session.commit()

    # 2. Add extracted fields
    fields = [
        ("product_name", "Dark Chocolate 70%"),
        ("brand_name", "ChocoArt"),
        ("mrp", "199.00"),
        ("net_quantity", "100 g"),
        ("quantity_unit", "g"),
        ("batch_number", "CH-2024-001"),
        ("manufacturing_date", "11/2024"),
        ("country_of_origin", "India"),
        ("manufacturer", "ChocoArt Confectionery Ltd, Mumbai 400001"),
        ("customer_care_details", "care@chocoart.in"),
    ]
    for name, val in fields:
        db_session.add(ExtractedField(
            verification_id=verification.id,
            field_name=name,
            field_value=val,
            confidence=0.92,
            source_text=f"{name}: {val}",
        ))
    db_session.commit()

    # 3. Unauthorized checks
    assert client.post(f"/api/verifications/{verification.id}/compliance").status_code == 401
    assert client.get(f"/api/verifications/{verification.id}/compliance").status_code == 401

    # 4. Non-existent verification ID check
    random_id = uuid.uuid4()
    assert client.post(f"/api/verifications/{random_id}/compliance", headers=auth_headers).status_code == 404
    assert client.get(f"/api/verifications/{random_id}/compliance", headers=auth_headers).status_code == 404

    # 5. Evaluate compliance (POST)
    post_res = client.post(f"/api/verifications/{verification.id}/compliance", headers=auth_headers)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["verification_id"] == str(verification.id)
    assert data["total_rules"] >= 10
    assert data["passed_rules"] >= 9
    assert data["overall_score"] is not None
    assert data["overall_score"] >= 90.0
    assert len(data["checks"]) == data["total_rules"]

    # 6. Retrieve compliance results (GET)
    get_res = client.get(f"/api/verifications/{verification.id}/compliance", headers=auth_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["verification_id"] == str(verification.id)
    assert get_data["overall_score"] == data["overall_score"]
    assert get_data["total_rules"] == data["total_rules"]

    # 7. Test Idempotent evaluation (repeated POST)
    repeat_res = client.post(f"/api/verifications/{verification.id}/compliance", headers=auth_headers)
    assert repeat_res.status_code == 200
    assert repeat_res.json()["total_rules"] == data["total_rules"]
