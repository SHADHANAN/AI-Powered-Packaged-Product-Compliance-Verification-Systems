import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    """Create a test client with foreign key enabled in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign key constraints enforcement
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


# ----------------------------------------------------------------------
# 1. USER INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_user_complete_lifecycle(client: TestClient):
    """Test full User lifecycle: create, list, retrieve, duplicate error, delete."""
    # 1. POST /api/users -> 201
    user_payload = {
        "name": "Inspector Sarah",
        "email": "sarah@metrology.gov",
        "password": "strongpassword123",
        "role": "inspector",
        "is_active": True,
    }
    create_res = client.post("/api/users", json=user_payload)
    assert create_res.status_code == 201
    created_user = create_res.json()
    user_id = created_user["id"]
    assert created_user["name"] == "Inspector Sarah"
    assert created_user["email"] == "sarah@metrology.gov"

    # 2. GET /api/users -> created user exists
    list_res = client.get("/api/users")
    assert list_res.status_code == 200
    user_ids = [u["id"] for u in list_res.json()]
    assert user_id in user_ids

    # 3. GET /api/users/{id} -> correct user returned
    get_res = client.get(f"/api/users/{user_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == user_id

    # 4. GET /api/users/{invalid-id} -> 404
    non_existent = str(uuid.uuid4())
    not_found_res = client.get(f"/api/users/{non_existent}")
    assert not_found_res.status_code == 404
    assert not_found_res.json()["success"] is False

    # 5. Duplicate email -> 400 Bad Request (clean error)
    dup_res = client.post("/api/users", json=user_payload)
    assert dup_res.status_code == 400
    assert dup_res.json()["success"] is False
    assert "already exists" in dup_res.json()["error"]["message"].lower()

    # 6. DELETE /api/users/{id} -> 204
    del_res = client.delete(f"/api/users/{user_id}")
    assert del_res.status_code == 204

    # 7. GET /api/users/{id} -> 404 after deletion
    get_deleted = client.get(f"/api/users/{user_id}")
    assert get_deleted.status_code == 404


# ----------------------------------------------------------------------
# 2. PRODUCT INTEGRATION TESTS
# ----------------------------------------------------------------------

def test_product_complete_lifecycle(client: TestClient):
    """Test full Product lifecycle: create, list, retrieve, delete."""
    # 1. POST /api/products -> 201
    prod_payload = {
        "product_name": "Premium Tea 250g",
        "brand_name": "TeaOrigin",
        "manufacturer": "TeaOrigin Plantations Ltd.",
        "mrp": 220.50,
        "net_quantity": "250g",
    }
    create_res = client.post("/api/products", json=prod_payload)
    assert create_res.status_code == 201
    product = create_res.json()
    prod_id = product["id"]
    assert product["product_name"] == "Premium Tea 250g"

    # 2. GET /api/products -> product exists
    list_res = client.get("/api/products")
    assert list_res.status_code == 200
    assert any(p["id"] == prod_id for p in list_res.json())

    # 3. GET /api/products/{id} -> correct product
    get_res = client.get(f"/api/products/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == prod_id

    # 4. GET invalid product ID -> 404
    assert client.get(f"/api/products/{uuid.uuid4()}").status_code == 404

    # 5. DELETE product -> 204
    assert client.delete(f"/api/products/{prod_id}").status_code == 204

    # 6. GET deleted product -> 404
    assert client.get(f"/api/products/{prod_id}").status_code == 404


# ----------------------------------------------------------------------
# 3. VERIFICATION INTEGRATION & FOREIGN KEY VALIDATION TESTS
# ----------------------------------------------------------------------

def test_verification_complete_lifecycle_and_fk_validation(client: TestClient):
    """Test Verification lifecycle and foreign key validation for product_id and inspector_id."""
    # Create User and Product
    u_res = client.post(
        "/api/users",
        json={"name": "Inspector Dave", "email": "dave@metrology.gov", "password": "password123"},
    )
    assert u_res.status_code == 201
    user_id = u_res.json()["id"]

    p_res = client.post(
        "/api/products",
        json={"product_name": "Herbal Shampoo 200ml", "brand_name": "AyurPure"},
    )
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    # 1. Attempt verification with non-existing product_id -> 404
    invalid_prod_res = client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/img1.jpg", "product_id": str(uuid.uuid4())},
    )
    assert invalid_prod_res.status_code == 404
    assert "product" in invalid_prod_res.json()["error"]["message"].lower()

    # 2. Attempt verification with non-existing inspector_id -> 404
    invalid_user_res = client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/img1.jpg", "inspector_id": str(uuid.uuid4())},
    )
    assert invalid_user_res.status_code == 404
    assert "user" in invalid_user_res.json()["error"]["message"].lower()

    # 3. POST /api/verifications with valid product_id and inspector_id -> 201
    v_res = client.post(
        "/api/verifications",
        json={
            "source_image_path": "uploads/img1.jpg",
            "product_id": prod_id,
            "inspector_id": user_id,
        },
    )
    assert v_res.status_code == 201
    verification = v_res.json()
    v_id = verification["id"]
    assert verification["product_id"] == prod_id
    assert verification["inspector_id"] == user_id
    assert verification["status"] == "pending"

    # 4. GET /api/verifications/{id} -> correct data
    get_res = client.get(f"/api/verifications/{v_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == v_id

    # 5. GET invalid verification ID -> 404
    assert client.get(f"/api/verifications/{uuid.uuid4()}").status_code == 404

    # 6. DELETE verification -> 204
    assert client.delete(f"/api/verifications/{v_id}").status_code == 204

    # 7. GET deleted verification -> 404
    assert client.get(f"/api/verifications/{v_id}").status_code == 404


# ----------------------------------------------------------------------
# 4. EXTRACTED FIELD INTEGRATION & FK VALIDATION TESTS
# ----------------------------------------------------------------------

def test_extracted_field_complete_lifecycle_and_fk_validation(client: TestClient):
    """Test ExtractedField lifecycle and verification_id FK validation."""
    # Create parent verification
    v_res = client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/pack.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Attempt creation with invalid verification_id -> 404
    invalid_v_res = client.post(
        "/api/extracted-fields",
        json={
            "verification_id": str(uuid.uuid4()),
            "field_name": "mrp",
            "field_value": "100.00",
        },
    )
    assert invalid_v_res.status_code == 404
    assert "verification" in invalid_v_res.json()["error"]["message"].lower()

    # 2. POST /api/extracted-fields with valid verification_id -> 201
    create_res = client.post(
        "/api/extracted-fields",
        json={
            "verification_id": v_id,
            "field_name": "mrp",
            "field_value": "100.00",
            "confidence": 0.96,
            "source_text": "MRP Rs 100.00",
        },
    )
    assert create_res.status_code == 201
    field_id = create_res.json()["id"]

    # 3. GET /api/extracted-fields/{id} -> 200
    get_res = client.get(f"/api/extracted-fields/{field_id}")
    assert get_res.status_code == 200
    assert get_res.json()["field_name"] == "mrp"

    # 4. DELETE -> 204
    assert client.delete(f"/api/extracted-fields/{field_id}").status_code == 204

    # 5. GET deleted resource -> 404
    assert client.get(f"/api/extracted-fields/{field_id}").status_code == 404


# ----------------------------------------------------------------------
# 5. COMPLIANCE CHECK INTEGRATION & FK VALIDATION TESTS
# ----------------------------------------------------------------------

def test_compliance_check_complete_lifecycle_and_fk_validation(client: TestClient):
    """Test ComplianceCheck lifecycle and verification_id FK validation."""
    v_res = client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/pack.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Invalid verification_id -> 404
    invalid_res = client.post(
        "/api/compliance-checks",
        json={
            "verification_id": str(uuid.uuid4()),
            "rule_code": "LM_01",
            "rule_name": "Name Rule",
            "status": "pass",
            "severity": "low",
            "message": "Valid name",
        },
    )
    assert invalid_res.status_code == 404

    # 2. Valid creation -> 201
    create_res = client.post(
        "/api/compliance-checks",
        json={
            "verification_id": v_id,
            "rule_code": "LM_01",
            "rule_name": "Name Rule",
            "status": "pass",
            "severity": "low",
            "message": "Valid name",
        },
    )
    assert create_res.status_code == 201
    check_id = create_res.json()["id"]

    # 3. GET -> 200
    assert client.get(f"/api/compliance-checks/{check_id}").status_code == 200

    # 4. DELETE -> 204
    assert client.delete(f"/api/compliance-checks/{check_id}").status_code == 204

    # 5. GET deleted resource -> 404
    assert client.get(f"/api/compliance-checks/{check_id}").status_code == 404


# ----------------------------------------------------------------------
# 6. REPORT INTEGRATION & FK VALIDATION TESTS
# ----------------------------------------------------------------------

def test_report_complete_lifecycle_and_fk_validation(client: TestClient):
    """Test Report lifecycle and verification_id FK validation."""
    v_res = client.post(
        "/api/verifications",
        json={"source_image_path": "uploads/pack.png"},
    )
    v_id = v_res.json()["id"]

    # 1. Invalid verification_id -> 404
    invalid_res = client.post(
        "/api/reports",
        json={
            "verification_id": str(uuid.uuid4()),
            "report_type": "pdf",
            "file_path": "reports/report.pdf",
        },
    )
    assert invalid_res.status_code == 404

    # 2. Valid creation -> 201
    create_res = client.post(
        "/api/reports",
        json={
            "verification_id": v_id,
            "report_type": "pdf",
            "file_path": "reports/report.pdf",
        },
    )
    assert create_res.status_code == 201
    report_id = create_res.json()["id"]

    # 3. GET -> 200
    assert client.get(f"/api/reports/{report_id}").status_code == 200

    # 4. DELETE -> 204
    assert client.delete(f"/api/reports/{report_id}").status_code == 204

    # 5. GET deleted resource -> 404
    assert client.get(f"/api/reports/{report_id}").status_code == 404


# ----------------------------------------------------------------------
# 7. CASCADE & RELATIONSHIP INTEGRATION TESTS (MANDATORY STEP 7)
# ----------------------------------------------------------------------

def test_verification_deletion_cascades_to_children(client: TestClient):
    """Verify deleting Verification cascades to ExtractedField, ComplianceCheck, and Report."""
    # 1. Create full hierarchy
    u_res = client.post(
        "/api/users",
        json={"name": "Inspector Bob", "email": "bob@gov.in", "password": "password123"},
    )
    assert u_res.status_code == 201
    user_id = u_res.json()["id"]

    p_res = client.post(
        "/api/products",
        json={"product_name": "Biscuits 100g", "brand_name": "SnackBite"},
    )
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    v_res = client.post(
        "/api/verifications",
        json={
            "source_image_path": "uploads/biscuit.jpg",
            "product_id": prod_id,
            "inspector_id": user_id,
        },
    )
    assert v_res.status_code == 201
    v_id = v_res.json()["id"]

    ef_res = client.post(
        "/api/extracted-fields",
        json={"verification_id": v_id, "field_name": "mrp", "field_value": "30.00"},
    )
    assert ef_res.status_code == 201
    ef_id = ef_res.json()["id"]

    cc_res = client.post(
        "/api/compliance-checks",
        json={
            "verification_id": v_id,
            "rule_code": "LM_MRP",
            "rule_name": "MRP Check",
            "status": "pass",
            "severity": "high",
            "message": "MRP declared",
        },
    )
    assert cc_res.status_code == 201
    cc_id = cc_res.json()["id"]

    r_res = client.post(
        "/api/reports",
        json={
            "verification_id": v_id,
            "report_type": "pdf",
            "file_path": "reports/biscuit.pdf",
        },
    )
    assert r_res.status_code == 201
    r_id = r_res.json()["id"]

    # 2. Delete the Verification
    del_res = client.delete(f"/api/verifications/{v_id}")
    assert del_res.status_code == 204

    # 3. Verify all children are cascadingly deleted -> 404
    assert client.get(f"/api/extracted-fields/{ef_id}").status_code == 404
    assert client.get(f"/api/compliance-checks/{cc_id}").status_code == 404
    assert client.get(f"/api/reports/{r_id}").status_code == 404

    # 4. Verify User and Product were NOT deleted
    assert client.get(f"/api/users/{user_id}").status_code == 200
    assert client.get(f"/api/products/{prod_id}").status_code == 200


def test_user_and_product_deletion_sets_null_on_verification(client: TestClient):
    """Verify deleting User or Product sets NULL on Verification foreign keys without deleting Verification."""
    # 1. Create User, Product, Verification
    u_res = client.post(
        "/api/users",
        json={"name": "Inspector Charlie", "email": "charlie@gov.in", "password": "password123"},
    )
    assert u_res.status_code == 201
    user_id = u_res.json()["id"]

    p_res = client.post(
        "/api/products",
        json={"product_name": "Juice 1L", "brand_name": "PureFruit"},
    )
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    v_res = client.post(
        "/api/verifications",
        json={
            "source_image_path": "uploads/juice.jpg",
            "product_id": prod_id,
            "inspector_id": user_id,
        },
    )
    assert v_res.status_code == 201
    v_id = v_res.json()["id"]

    # 2. Delete User
    del_u = client.delete(f"/api/users/{user_id}")
    assert del_u.status_code == 204

    # Verification still exists and inspector_id is None
    v_after_u = client.get(f"/api/verifications/{v_id}")
    assert v_after_u.status_code == 200
    assert v_after_u.json()["inspector_id"] is None
    assert v_after_u.json()["product_id"] == prod_id

    # 3. Delete Product
    del_p = client.delete(f"/api/products/{prod_id}")
    assert del_p.status_code == 204

    # Verification still exists and product_id is None
    v_after_p = client.get(f"/api/verifications/{v_id}")
    assert v_after_p.status_code == 200
    assert v_after_p.json()["product_id"] is None
    assert v_after_p.json()["inspector_id"] is None
