import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient instance for testing endpoints."""
    with TestClient(app) as test_client:
        yield test_client
