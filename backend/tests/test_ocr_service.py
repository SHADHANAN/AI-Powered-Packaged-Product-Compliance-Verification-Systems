import io
import os
import subprocess
import pytest
from PIL import Image

from app.services import image_service, ocr_service
from app.utils import image_processing
from app.utils.exceptions import BadRequestException, NotFoundException


def create_test_image_file(text_desc: str = "test") -> str:
    """Helper to save a valid test image to disk and return its path."""
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 100), color="white")
    img.save(buf, format="JPEG")
    return image_service.save_image_file(buf.getvalue(), f"{text_desc}.jpg")


def test_ocr_service_empty_or_nonexistent_image():
    """Ensure ocr_service raises BadRequestException for empty or non-existent paths."""
    with pytest.raises(BadRequestException):
        ocr_service.extract_text_from_image("")

    with pytest.raises(BadRequestException):
        ocr_service.extract_text_from_image("nonexistent/path/to/image.jpg")


def test_ocr_service_valid_image(monkeypatch):
    """Test OCR service execution on a valid image."""
    image_path = create_test_image_file("valid_ocr")
    try:
        sample_text = "M.R.P. Rs. 250.00\nNET WT: 500g\nMFG DATE: 12/2024\nBATCH: B-101"

        # Mock tesseract command detection and subprocess execution
        monkeypatch.setattr(ocr_service, "get_tesseract_command", lambda: "mock_tesseract")

        class MockCompletedProcess:
            returncode = 0
            stdout = sample_text
            stderr = ""

        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: MockCompletedProcess())

        result_text = ocr_service.extract_text_from_image(image_path)
        assert "250.00" in result_text
        assert "500g" in result_text
    finally:
        image_service.delete_image_file(image_path)


def test_ocr_service_handles_missing_tesseract_gracefully(monkeypatch):
    """Test OCR service returns fallback string when Tesseract binary is not installed."""
    image_path = create_test_image_file("tesseract_missing")
    try:
        monkeypatch.setattr(ocr_service, "get_tesseract_command", lambda: None)
        result = ocr_service.extract_text_from_image(image_path)
        assert result == ""
    finally:
        image_service.delete_image_file(image_path)


def test_image_preprocessing_pipeline():
    """Test preprocessing utility functions."""
    image_path = create_test_image_file("preprocess_test")
    try:
        processed_img = image_processing.preprocess_image_for_ocr(image_path)
        assert processed_img is not None
        assert processed_img.mode == "L"  # Grayscale
    finally:
        image_service.delete_image_file(image_path)
