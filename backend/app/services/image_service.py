import os
import uuid
from typing import Optional

from app.config import get_settings
from app.utils.exceptions import InternalServerErrorException
from app.utils.file_validation import sanitize_filename
from app.utils.logging import get_logger

logger = get_logger("app.services.image")
settings = get_settings()


def save_image_file(content: bytes, original_filename: str, target_dir: Optional[str] = None) -> str:
    """Safely store an image binary with a unique UUID filename to prevent path traversal.
    
    Returns the normalized relative storage path.
    """
    upload_dir = target_dir or settings.UPLOAD_DIR
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception as exc:
        logger.error(f"Failed to create upload directory '{upload_dir}': {exc}", exc_info=True)
        raise InternalServerErrorException("Failed to initialize storage directory for image upload")

    clean_filename = sanitize_filename(original_filename)
    _, ext = os.path.splitext(clean_filename)
    ext_lower = ext.lower() if ext else ".jpg"
    if ext_lower == ".jpeg":
        ext_lower = ".jpg"

    unique_filename = f"{uuid.uuid4().hex}{ext_lower}"
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        logger.error(f"Failed to write image to disk '{file_path}': {exc}", exc_info=True)
        raise InternalServerErrorException("Failed to persist uploaded image file to disk")

    normalized_path = file_path.replace("\\", "/")
    logger.info(f"Successfully saved uploaded image to '{normalized_path}'")
    return normalized_path


def delete_image_file(file_path: str) -> bool:
    """Safely delete an uploaded image file if it exists.
    
    Used for cleanup on aborted or failed operations.
    """
    if not file_path:
        return False
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up image file '{file_path}'")
            return True
        return False
    except Exception as exc:
        logger.warning(f"Failed to delete image file '{file_path}': {exc}")
        return False
