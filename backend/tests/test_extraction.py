"""Unit tests for the AI-assisted OCR field interpretation service."""
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.extraction_service.service import interpret_product_fields


@pytest.fixture(autouse=True)
def cleanup_settings():
    """Reset configuration cache after each test to prevent pollution."""
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_interpret_product_fields_normal(monkeypatch):
    """Test normal OCR input interpretation using Mock AI provider."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    ocr_text = (
        "M.R.P. : Rs. 199/-\n"
        "NET QTY: 500 gms\n"
        "BRAND: Fresh Foods"
    )

    results = interpret_product_fields(ocr_text)

    # Convert results list to dict for easier assertions
    res_map = {item["field"]: item for item in results}

    assert res_map["mrp"]["status"] == "COMPLETED"
    assert res_map["mrp"]["interpreted_value"] == "199.00"
    assert res_map["net_quantity"]["interpreted_value"] == "500 gms"
    assert res_map["brand_name"]["interpreted_value"] == "Fresh Foods"


def test_interpret_product_fields_ambiguous(monkeypatch):
    """Test ambiguous OCR input interpretation using Mock AI provider."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    ocr_text = "MRP: Rs. 1O0"  # Contains letter O instead of number 0

    results = interpret_product_fields(ocr_text)
    res_map = {item["field"]: item for item in results}

    assert res_map["mrp"]["status"] == "COMPLETED"
    assert res_map["mrp"]["interpreted_value"] == "100.00"
    assert res_map["mrp"]["original_ocr_value"] == "1O0"
    assert "Corrected letter" in res_map["mrp"]["short_reason"]


def test_interpret_product_fields_low_confidence(monkeypatch):
    """Test smudged/low confidence OCR input interpretation."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    ocr_text = "The label is extremely SMUDGE and unreadable here"

    results = interpret_product_fields(ocr_text)
    res_map = {item["field"]: item for item in results}

    # All fields should flag NEEDS_REVIEW
    for f in res_map.values():
        assert f["status"] == "NEEDS_REVIEW"
        assert f["confidence"] == 0.3
        assert "smudged/unreadable" in f["short_reason"]


def test_interpret_product_fields_empty(monkeypatch):
    """Test empty OCR input interpretation."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    results = interpret_product_fields("   ")
    res_map = {item["field"]: item for item in results}

    # All fields should be UNRESOLVED with null values
    for f in res_map.values():
        assert f["status"] == "UNRESOLVED"
        assert f["confidence"] == 0.0
        assert f["interpreted_value"] is None
        assert f["original_ocr_value"] is None


def test_interpret_product_fields_fallback(monkeypatch):
    """Test that if AI fails/is disabled, it falls back to deterministic extraction."""
    monkeypatch.setenv("AI_ENABLED", "False")
    get_settings.cache_clear()

    ocr_text = (
        "M.R.P. : Rs. 199/-\n"
        "NET QTY: 500 gms"
    )

    results = interpret_product_fields(ocr_text)
    res_map = {item["field"]: item for item in results}

    # Deterministic fallback should populate mrp and net_quantity
    assert res_map["mrp"]["status"] == "COMPLETED"
    assert res_map["mrp"]["interpreted_value"] == "199"  # deterministic regex output
    assert res_map["net_quantity"]["interpreted_value"] == "500 gms"
    # Unmatched fields should be UNRESOLVED
    assert res_map["brand_name"]["status"] == "UNRESOLVED"


def test_api_interpret_ocr_endpoint(client, monkeypatch):
    """Test interpretation API endpoint workflow using Mock AI provider."""
    monkeypatch.setenv("AI_ENABLED", "True")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    payload = {
        "ocr_text": "M.R.P. : Rs. 199/-\nNET QTY: 500 gms"
    }

    response = client.post("/api/extraction/interpret", json=payload)
    assert response.status_code == 200

    results = response.json()
    assert len(results) >= 10

    res_map = {item["field"]: item for item in results}
    assert res_map["mrp"]["interpreted_value"] == "199.00"
    assert res_map["mrp"]["status"] == "COMPLETED"
    assert res_map["net_quantity"]["interpreted_value"] == "500 gms"
