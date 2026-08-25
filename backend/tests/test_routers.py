import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def test_client():
    """FastAPI TestClient with overridden get_db dependency yielding SQLite in-memory session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_users_router_crud(test_client: TestClient):
    """Test /api/users endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # 1. Create User
    res = test_client.post(
        "/api/users",
        json={
            "name": "Inspector John",
            "email": "john@inspection.gov",
            "password": "password123",
            "role": "inspector",
            "is_active": True,
        },
    )
    assert res.status_code == 201
    user_data = res.json()
    user_id = user_data["id"]
    assert user_data["email"] == "john@inspection.gov"

    # 2. List Users
    res = test_client.get("/api/users")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get User by ID
    res = test_client.get(f"/api/users/{user_id}")
    assert res.status_code == 200
    assert res.json()["id"] == user_id

    # 4. Delete User
    res = test_client.delete(f"/api/users/{user_id}")
    assert res.status_code == 204

    # 5. Not Found 404
    res = test_client.get(f"/api/users/{user_id}")
    assert res.status_code == 404
    assert res.json()["success"] is False


def test_products_router_crud(test_client: TestClient):
    """Test /api/products endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # 1. Create Product
    res = test_client.post(
        "/api/products",
        json={
            "product_name": "Dark Chocolate 100g",
            "brand_name": "ChocoDelight",
            "mrp": 150.00,
            "net_quantity": "100g",
        },
    )
    assert res.status_code == 201
    prod_data = res.json()
    prod_id = prod_data["id"]
    assert prod_data["product_name"] == "Dark Chocolate 100g"

    # 2. List Products
    res = test_client.get("/api/products")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get Product by ID
    res = test_client.get(f"/api/products/{prod_id}")
    assert res.status_code == 200
    assert res.json()["id"] == prod_id

    # 4. Delete Product
    res = test_client.delete(f"/api/products/{prod_id}")
    assert res.status_code == 204

    # 5. Not Found
    res = test_client.get(f"/api/products/{prod_id}")
    assert res.status_code == 404


def test_verifications_router_crud(test_client: TestClient):
    """Test /api/verifications endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # 1. Create Verification
    res = test_client.post(
        "/api/verifications",
        json={
            "source_image_path": "uploads/packaged_item.png",
        },
    )
    assert res.status_code == 201
    v_data = res.json()
    v_id = v_data["id"]
    assert v_data["status"] == "pending"

    # 2. List Verifications
    res = test_client.get("/api/verifications")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get by ID
    res = test_client.get(f"/api/verifications/{v_id}")
    assert res.status_code == 200
    assert res.json()["id"] == v_id

    # 4. Delete
    res = test_client.delete(f"/api/verifications/{v_id}")
    assert res.status_code == 204

    # 5. Not Found
    res = test_client.get(f"/api/verifications/{v_id}")
    assert res.status_code == 404


def test_extracted_fields_router_crud(test_client: TestClient):
    """Test /api/extracted-fields endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # Create parent verification
    v_res = test_client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/item.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Create Extracted Field
    res = test_client.post(
        "/api/extracted-fields",
        json={
            "verification_id": v_id,
            "field_name": "mrp",
            "field_value": "150.00",
            "confidence": 0.99,
            "source_text": "MRP Rs 150.00",
        },
    )
    assert res.status_code == 201
    ef_data = res.json()
    ef_id = ef_data["id"]

    # 2. List Extracted Fields
    res = test_client.get("/api/extracted-fields")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get by ID
    res = test_client.get(f"/api/extracted-fields/{ef_id}")
    assert res.status_code == 200
    assert res.json()["id"] == ef_id

    # 4. Delete
    res = test_client.delete(f"/api/extracted-fields/{ef_id}")
    assert res.status_code == 204

    # 5. Not Found
    res = test_client.get(f"/api/extracted-fields/{ef_id}")
    assert res.status_code == 404


def test_compliance_checks_router_crud(test_client: TestClient):
    """Test /api/compliance-checks endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # Create parent verification
    v_res = test_client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/item.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Create Compliance Check
    res = test_client.post(
        "/api/compliance-checks",
        json={
            "verification_id": v_id,
            "rule_code": "LM_MRP_RULE",
            "rule_name": "MRP Display Rule",
            "status": "pass",
            "severity": "high",
            "message": "MRP declared properly",
        },
    )
    assert res.status_code == 201
    cc_data = res.json()
    cc_id = cc_data["id"]

    # 2. List Compliance Checks
    res = test_client.get("/api/compliance-checks")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get by ID
    res = test_client.get(f"/api/compliance-checks/{cc_id}")
    assert res.status_code == 200
    assert res.json()["id"] == cc_id

    # 4. Delete
    res = test_client.delete(f"/api/compliance-checks/{cc_id}")
    assert res.status_code == 204

    # 5. Not Found
    res = test_client.get(f"/api/compliance-checks/{cc_id}")
    assert res.status_code == 404


def test_reports_router_crud(test_client: TestClient):
    """Test /api/reports endpoints for POST, GET, GET by ID, DELETE, and 404."""
    # Create parent verification
    v_res = test_client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/item.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Create Report
    res = test_client.post(
        "/api/reports",
        json={
            "verification_id": v_id,
            "report_type": "pdf",
            "file_path": "reports/report_001.pdf",
        },
    )
    assert res.status_code == 201
    r_data = res.json()
    r_id = r_data["id"]

    # 2. List Reports
    res = test_client.get("/api/reports")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get by ID
    res = test_client.get(f"/api/reports/{r_id}")
    assert res.status_code == 200
    assert res.json()["id"] == r_id

    # 4. Delete
    res = test_client.delete(f"/api/reports/{r_id}")
    assert res.status_code == 204

    # 5. Not Found
    res = test_client.get(f"/api/reports/{r_id}")
    assert res.status_code == 404


def test_openapi_schema_contains_all_crud_paths(test_client: TestClient):
    """Verify that OpenAPI schema includes all 6 CRUD router path declarations."""
    res = test_client.get("/api/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    expected_routes = [
        "/api/users",
        "/api/users/{id}",
        "/api/products",
        "/api/products/{id}",
        "/api/verifications",
        "/api/verifications/{id}",
        "/api/extracted-fields",
        "/api/extracted-fields/{id}",
        "/api/compliance-checks",
        "/api/compliance-checks/{id}",
        "/api/reports",
        "/api/reports/{id}",
        "/api/health",
        "/api/health/db",
    ]

    for route in expected_routes:
        assert route in paths, f"Route '{route}' is missing from OpenAPI paths"
