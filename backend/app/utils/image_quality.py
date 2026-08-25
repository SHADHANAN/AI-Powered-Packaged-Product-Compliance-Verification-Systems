from PIL import ImageFilter, ImageStat

from app.utils.exceptions import BadRequestException
from app.utils.image_processing import load_image


def assess_image_quality(image_path: str) -> dict:
    """Calculate basic image-quality metrics relevant to OCR."""

    try:
        image = load_image(image_path)
    except Exception as exc:
        raise BadRequestException(f"Unable to assess image quality: {exc}") from exc

    grayscale = image.convert("L")
    stats = ImageStat.Stat(grayscale)

    mean_brightness = round(stats.mean[0], 2)
    contrast = round(stats.stddev[0], 2)

    # Edge strength provides a lightweight sharpness indicator.
    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_stats = ImageStat.Stat(edges)
    sharpness = round(edge_stats.mean[0], 2)

    width, height = grayscale.size

    return {
        "width": width,
        "height": height,
        "brightness": mean_brightness,
        "contrast": contrast,
        "sharpness": sharpness,
    }