import subprocess
from typing import Optional

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("app.orientation")

settings = get_settings()


def detect_orientation(image_path: str) -> Optional[int]:
    """
    Detect the clockwise rotation required to make the image upright.

    Returns:
        0, 90, 180, or 270 degrees when orientation is detected reliably.
        None when detection fails or confidence is too low.
    """

    if not image_path:
        return None

    tesseract_cmd = settings.TESSERACT_CMD or "tesseract"

    command = [
        tesseract_cmd,
        image_path,
        "stdout",
        "--psm",
        "0",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=settings.OCR_TIMEOUT_SECONDS,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(
                "Tesseract orientation detection failed: %s",
                result.stderr.strip(),
            )
            return None

        output = result.stdout

        rotation = None
        confidence = None

        for line in output.splitlines():
            if line.startswith("Rotate:"):
                rotation = int(line.split(":", 1)[1].strip())

            elif line.startswith("Orientation confidence:"):
                confidence = float(line.split(":", 1)[1].strip())

        if rotation not in {0, 90, 180, 270}:
            return None

        if confidence is None or confidence < 5.0:
            logger.warning(
                "Orientation confidence too low: %s",
                confidence,
            )
            return None

        logger.info(
            "Detected image rotation: %s degrees (confidence %.2f)",
            rotation,
            confidence,
        )

        return rotation

    except (subprocess.TimeoutExpired, ValueError) as exc:
        logger.warning("Orientation detection failed: %s", exc)
        return None

    except Exception as exc:
        logger.error(
            "Unexpected orientation detection error: %s",
            exc,
            exc_info=True,
        )
        return None