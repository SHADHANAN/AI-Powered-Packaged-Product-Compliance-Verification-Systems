"""High-level field extraction service."""

from typing import Any, Dict, List

from app.services.field_extraction_service import extract_fields_from_text


def extract_product_fields(raw_text: str) -> List[Dict[str, Any]]:
    """Extract structured product fields from OCR text."""
    return extract_fields_from_text(raw_text)