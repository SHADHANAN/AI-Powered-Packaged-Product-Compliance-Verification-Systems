"""Utilities for normalizing OCR text before field extraction."""

import re
import unicodedata


def normalize_ocr_text(text: str) -> str:
    """Normalize common OCR formatting issues without changing meaning."""
    if not text:
        return ""

    # Normalize Unicode characters such as different dash/quote variants.
    text = unicodedata.normalize("NFKC", text)

    # Normalize common OCR currency/spacing representations.
    text = text.replace("₹", " Rs ")
    text = text.replace("â‚¹", " Rs ")

    # Normalize common separators while preserving useful punctuation.
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    # Collapse repeated whitespace.
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize spaces around common field separators.
    text = re.sub(r"\s*:\s*", ": ", text)


    # Remove excessive blank lines.
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()