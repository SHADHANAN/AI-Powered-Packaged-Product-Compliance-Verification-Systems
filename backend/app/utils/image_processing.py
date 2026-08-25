import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

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


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Enhance contrast of an image to improve OCR legibility."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def enhance_sharpness(image: Image.Image, factor: float = 1.3) -> Image.Image:
    """Enhance sharpness of an image."""
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def resize_for_ocr(image: Image.Image, min_dimension: int = 800, max_dimension: int = 2400) -> Image.Image:
    """Scale small images up or very large images down for optimal OCR processing."""
    width, height = image.size
    min_side = min(width, height)
    max_side = max(width, height)

    if min_side < min_dimension and min_side > 0:
        scale = min_dimension / min_side
        new_size = (int(width * scale), int(height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)
    elif max_side > max_dimension:
        scale = max_dimension / max_side
        new_size = (int(width * scale), int(height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)
    return image


def preprocess_image_for_ocr(image_path: str) -> Image.Image:
    """Run full deterministic preprocessing pipeline on a stored image."""
    image = load_image(image_path)
    
    # 1. Convert to RGB / Grayscale
    gray = to_grayscale(image)

    # 2. Resize if necessary
    resized = resize_for_ocr(gray)

    # 3. Enhance contrast
    contrasted = enhance_contrast(resized, factor=1.5)

    # 4. Enhance sharpness
    sharp = enhance_sharpness(contrasted, factor=1.2)

    logger.debug(f"Preprocessed image '{image_path}' -> {sharp.size}")
    return sharp
