"""High-level field extraction service."""

from typing import Any, Dict, List

from app.services.field_extraction_service import extract_fields_from_text, interpret_ocr_fields


def extract_product_fields(raw_text: str) -> List[Dict[str, Any]]:
    """Extract structured product fields from OCR text."""
    return extract_fields_from_text(raw_text)


def interpret_product_fields(raw_text: str) -> List[Dict[str, Any]]:
    """Interpret product fields from raw OCR text with AI assistance and fallback."""
    return interpret_ocr_fields(raw_text)