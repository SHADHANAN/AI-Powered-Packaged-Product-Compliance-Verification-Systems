from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test GET /api/health returns 200 with correct payload (Phase 1 contract preserved)."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "product-compliance-backend"


def test_database_health_endpoint(client: TestClient):
    """Test GET /api/health/db returns 200 and connectivity status."""
    response = client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["connected", "disconnected"]
    assert data["database"] == "postgresql"


def test_root_endpoint(client: TestClient):
    """Test GET / returns 200 and identifies running status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data["message"].lower()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert data["docs_url"] == "/docs"


def test_swagger_documentation(client: TestClient):
    """Test GET /docs returns 200."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_documentation(client: TestClient):
    """Test GET /redoc returns 200."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """Test GET /api/openapi.json returns valid OpenAPI JSON."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert "/api/health" in data["paths"]
    assert "/api/health/db" in data["paths"]


def test_not_found_exception_handling(client: TestClient):
    """Test that 404 returns structured JSON response."""
    response = client.get("/api/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["status_code"] == 404
