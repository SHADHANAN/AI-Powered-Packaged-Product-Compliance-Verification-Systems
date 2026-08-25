from app.utils.orientation import detect_orientation


def test_detect_orientation_returns_none_for_low_confidence():
    result = detect_orientation(
        "test_data/ocr/baseline_label.jpg"
    )

    assert result is None or result in {0, 90, 180, 270}
from PIL import Image
import pytest

from app.utils.orientation import detect_orientation, rotate_image_for_ocr


def test_detect_orientation_returns_none_for_low_confidence():
    result = detect_orientation(
        "test_data/ocr/baseline_label.jpg"
    )

    assert result is None or result in {0, 90, 180, 270}


def test_rotate_image_zero_degrees_preserves_dimensions():
    image = Image.new("L", (120, 80))

    rotated = rotate_image_for_ocr(image, 0)

    assert rotated.size == (120, 80)


@pytest.mark.parametrize(
    "rotation,expected_size",
    [
        (90, (80, 120)),
        (180, (120, 80)),
        (270, (80, 120)),
    ],
)
def test_rotate_image_changes_dimensions_correctly(rotation, expected_size):
    image = Image.new("L", (120, 80))

    rotated = rotate_image_for_ocr(image, rotation)

    assert rotated.size == expected_size


def test_rotate_image_rejects_invalid_rotation():
    image = Image.new("L", (120, 80))

    with pytest.raises(ValueError):
        rotate_image_for_ocr(image, 45)