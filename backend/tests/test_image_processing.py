from PIL import Image

from app.utils.image_processing import resize_for_ocr


def test_resize_for_ocr_upscales_small_image():
    image = Image.new("L", (400, 200))

    resized = resize_for_ocr(image)

    assert resized.size == (2400, 1200)


def test_resize_for_ocr_downscales_large_image():
    image = Image.new("L", (4800, 2400))

    resized = resize_for_ocr(image)

    assert resized.size == (2400, 1200)


def test_resize_for_ocr_preserves_supported_size():
    image = Image.new("L", (1600, 1200))

    resized = resize_for_ocr(image)

    assert resized.size == (1600, 1200)
def test_reduce_noise_preserves_image_dimensions():
    image = Image.new("L", (1200, 1200))

    from app.utils.image_processing import reduce_noise

    filtered = reduce_noise(image)

    assert filtered.size == image.size
    assert filtered.mode == image.mode


def test_reduce_noise_rejects_invalid_filter_size():
    from app.utils.image_processing import reduce_noise

    image = Image.new("L", (100, 100))

    try:
        reduce_noise(image, size=4)
        assert False, "Expected ValueError for even filter size"
    except ValueError:
        pass
from app.utils.image_processing import (
    enhance_contrast,
    enhance_sharpness,
)


def test_enhance_contrast_preserves_image_properties():
    image = Image.new("L", (800, 600), color=128)

    enhanced = enhance_contrast(image, factor=1.5)

    assert enhanced.size == image.size
    assert enhanced.mode == image.mode


def test_enhance_sharpness_preserves_image_properties():
    image = Image.new("L", (800, 600), color=128)

    enhanced = enhance_sharpness(image, factor=1.3)

    assert enhanced.size == image.size
    assert enhanced.mode == image.mode


def test_enhance_contrast_rejects_invalid_factor():
    image = Image.new("L", (100, 100))

    try:
        enhance_contrast(image, factor=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_enhance_sharpness_rejects_invalid_factor():
    image = Image.new("L", (100, 100))

    try:
        enhance_sharpness(image, factor=-1)
        assert False, "Expected ValueError"
    except ValueError:
        pass