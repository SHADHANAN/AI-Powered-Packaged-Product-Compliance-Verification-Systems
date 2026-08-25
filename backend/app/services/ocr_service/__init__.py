from app.services.ocr_service.service import (
    extract_text_from_image,
    get_tesseract_command,
)

__all__ = [
    "extract_text_from_image",
    "get_tesseract_command",
]