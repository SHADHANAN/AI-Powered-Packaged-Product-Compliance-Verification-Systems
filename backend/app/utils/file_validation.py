import io
import os
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.utils.exceptions import BadRequestException, PayloadTooLargeException
from app.utils.logging import get_logger

logger = get_logger("app.file_validation")
settings = get_settings()

PIL_FORMAT_MAPPING = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal attempts."""
    base_name = os.path.basename(filename)
    # Remove any potential path traversal or null characters
    clean_name = base_name.replace("\x00", "").strip()
    return clean_name


def validate_image_file(file: UploadFile) -> bytes:
    """Validate uploaded image extension, MIME type, size, and binary integrity.
    
    Returns raw file bytes upon successful validation.
    Raises BadRequestException or PayloadTooLargeException on failure.
    """
    if not file or not file.filename:
        raise BadRequestException("No image file was provided for upload")

    clean_filename = sanitize_filename(file.filename)
    _, ext = os.path.splitext(clean_filename)
    ext_lower = ext.lower()

    # 1. Extension validation
    if ext_lower not in settings.ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)
        raise BadRequestException(
            f"Unsupported file extension '{ext}'. Allowed extensions: {allowed}"
        )

    # 2. MIME type validation (from header if present)
    if file.content_type and file.content_type.lower() not in settings.ALLOWED_IMAGE_MIME_TYPES:
        allowed_mimes = ", ".join(settings.ALLOWED_IMAGE_MIME_TYPES)
        raise BadRequestException(
            f"Unsupported content type '{file.content_type}'. Allowed types: {allowed_mimes}"
        )

    # 3. Read content and validate size
    try:
        content = file.file.read()
    except Exception as exc:
        logger.warning(f"Failed to read uploaded file stream: {exc}")
        raise BadRequestException("Could not read uploaded file content")

    if not content or len(content) == 0:
        raise BadRequestException("Uploaded file is empty (0 bytes)")

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise PayloadTooLargeException(
            f"File size ({len(content)} bytes) exceeds the maximum limit of {max_mb} MB"
        )

    # 4. Deep binary integrity validation via Pillow
    try:
        image_stream = io.BytesIO(content)
        with Image.open(image_stream) as img:
            img.verify()
            detected_format = img.format
            if detected_format not in PIL_FORMAT_MAPPING:
                raise BadRequestException(
                    f"Unsupported image format '{detected_format}'. Must be JPEG, PNG, or WebP"
                )
    except (UnidentifiedImageError, SyntaxError, ValueError) as exc:
        logger.warning(f"Corrupted or non-image file upload attempt: {exc}")
        raise BadRequestException("Uploaded file is corrupted or is not a valid image")
    except Exception as exc:
        logger.warning(f"Image verification error: {exc}")
        raise BadRequestException("Uploaded file is not a valid image")

    return content
