import os
import shutil
import subprocess
import tempfile
from typing import Optional

from app.config import get_settings
from app.utils.exceptions import BadRequestException, InternalServerErrorException
from app.utils.image_processing import preprocess_image_for_ocr
from app.utils.logging import get_logger

logger = get_logger("app.services.ocr")
settings = get_settings()


def get_tesseract_command() -> Optional[str]:
    """Find the path to the Tesseract OCR binary."""
    if settings.TESSERACT_CMD and os.path.isfile(settings.TESSERACT_CMD):
        return settings.TESSERACT_CMD

    # Check default PATH
    found = shutil.which("tesseract")
    if found:
        return found

    # Check standard Windows paths
    common_windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for path in common_windows_paths:
        if os.path.isfile(path):
            return path

    return None


def extract_text_from_image(image_path: str) -> str:
    """Run OCR extraction pipeline on a stored product label image.

    1. Validates and preprocesses image with Pillow.
    2. Executes Tesseract OCR via subprocess.
    3. Returns cleaned raw extracted text string.
    """
    if not image_path:
        raise BadRequestException("Image path cannot be empty")

    if not os.path.exists(image_path):
        raise BadRequestException(f"Image not found at path: {image_path}")

    # 1. Preprocess image with Pillow
    preprocessed_img = preprocess_image_for_ocr(image_path)

    # 2. Check for Tesseract OCR executable
    tesseract_cmd = get_tesseract_command()

    if not tesseract_cmd:
        logger.warning(
            "Tesseract OCR binary not found on the host system. "
            "Returning empty OCR text fallback."
        )
        return ""

    # 3. Save preprocessed image to a temporary file
    temp_fd, temp_img_path = tempfile.mkstemp(suffix=".png")
    os.close(temp_fd)

    try:
        preprocessed_img.save(temp_img_path, format="PNG")

        cmd = [
            tesseract_cmd,
            temp_img_path,
            "stdout",
            "-l",
            settings.OCR_LANGUAGE,
            "--psm",
            str(settings.OCR_PSM),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=settings.OCR_TIMEOUT_SECONDS,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(
                f"Tesseract returned non-zero code "
                f"{result.returncode}: {result.stderr}"
            )
            return ""

        cleaned_text = result.stdout.strip()

        logger.info(
            f"Successfully extracted {len(cleaned_text)} characters of OCR text"
        )

        return cleaned_text

    except subprocess.TimeoutExpired:
        logger.error(
            f"Tesseract OCR timed out after "
            f"{settings.OCR_TIMEOUT_SECONDS}s"
        )
        raise InternalServerErrorException("OCR processing timed out")

    except Exception as exc:
        logger.error(
            f"Unexpected error during OCR text extraction: {exc}",
            exc_info=True,
        )
        raise InternalServerErrorException(
            "Failed to extract text from product image"
        )

    finally:
        if os.path.exists(temp_img_path):
            try:
                os.remove(temp_img_path)
            except Exception:
                pass