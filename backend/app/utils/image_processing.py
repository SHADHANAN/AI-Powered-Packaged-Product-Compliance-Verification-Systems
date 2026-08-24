import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
from app.utils.orientation import detect_orientation, rotate_image_for_ocr
from app.utils.exceptions import BadRequestException, NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.image_processing")


def load_image(image_path: str) -> Image.Image:
    """Safely load an image from disk."""
    if not os.path.exists(image_path):
        logger.warning(f"Image not found at path '{image_path}'")
        raise NotFoundException(f"Image file not found at '{image_path}'")
    try:
        img = Image.open(image_path)
        img.load()  # Force load binary
        return img
    except (UnidentifiedImageError, ValueError) as exc:
        logger.warning(f"Failed to identify image at '{image_path}': {exc}")
        raise BadRequestException("Cannot load image: file is corrupted or not a valid image format")
    except Exception as exc:
        logger.error(f"Error opening image file '{image_path}': {exc}", exc_info=True)
        raise BadRequestException("Failed to read image from storage")


def to_grayscale(image: Image.Image) -> Image.Image:
    """Convert an RGB/RGBA image to grayscale (L mode)."""
    return ImageOps.grayscale(image)
def reduce_noise(image: Image.Image, size: int = 3) -> Image.Image:
    """Reduce small-scale image noise while preserving text edges."""
    if size < 3 or size % 2 == 0:
        raise ValueError("Noise filter size must be an odd value >= 3")

    return image.filter(ImageFilter.MedianFilter(size=size))

def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Enhance image contrast for OCR while validating the enhancement factor."""
    if factor <= 0:
        raise ValueError("Contrast factor must be greater than zero")

    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def enhance_sharpness(image: Image.Image, factor: float = 1.3) -> Image.Image:
    """Enhance image sharpness for OCR while validating the enhancement factor."""
    if factor <= 0:
        raise ValueError("Sharpness factor must be greater than zero")

    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)

def resize_for_ocr(
    image: Image.Image,
    min_dimension: int = 1200,
    max_dimension: int = 2400,
) -> Image.Image:
    """Resize an image to an OCR-friendly range while preserving aspect ratio."""

    width, height = image.size

    if width <= 0 or height <= 0:
        return image

    shortest_side = min(width, height)
    longest_side = max(width, height)

    # Upscale small images so small label text has enough pixels.
    if shortest_side < min_dimension:
        scale = min_dimension / shortest_side
    # Downscale very large images to avoid unnecessary OCR cost.
    elif longest_side > max_dimension:
        scale = max_dimension / longest_side
    else:
        return image

    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )


def preprocess_image_for_ocr(image_path: str) -> Image.Image:
    """Run the complete deterministic preprocessing pipeline for OCR."""
    image = load_image(image_path)

    # 1. Detect orientation before other transformations.
    rotation = detect_orientation(image_path)

    # 2. Rotate only when orientation detection is reliable.
    if rotation is not None:
        image = rotate_image_for_ocr(image, rotation)
        logger.debug(
            f"Applied OCR orientation correction: {rotation} degrees"
        )
    else:
        logger.debug(
            "OCR orientation correction skipped because confidence was insufficient"
        )

    # 3. Convert to grayscale.
    gray = to_grayscale(image)

    # 4. Resize for OCR.
    resized = resize_for_ocr(gray)

    # 5. Reduce image noise.
    denoised = reduce_noise(resized, size=3)

    # 6. Enhance contrast.
    contrasted = enhance_contrast(denoised, factor=1.5)

    # 7. Enhance sharpness.
    sharp = enhance_sharpness(contrasted, factor=1.2)

    logger.debug(
        f"Preprocessed image '{image_path}' -> {sharp.size}"
    )

    return sharp