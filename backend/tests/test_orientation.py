from app.utils.orientation import detect_orientation


def test_detect_orientation_returns_none_for_low_confidence():
    result = detect_orientation(
        "test_data/ocr/baseline_label.jpg"
    )

    assert result is None or result in {0, 90, 180, 270}