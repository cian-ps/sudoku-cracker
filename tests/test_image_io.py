from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import numpy as np
from PIL import Image

from modules.image_io import _decode_bgr_from_bytes, load_bgr_image


def test_load_bgr_image_delegates_to_imread_for_paths() -> None:
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with (
        patch("modules.image_io.is_android", return_value=False),
        patch("modules.image_io.cv2.imread", return_value=frame) as mock_imread,
    ):
        result = load_bgr_image("/tmp/puzzle.png")

    mock_imread.assert_called_once_with("/tmp/puzzle.png")
    assert result is frame


def test_load_bgr_image_uses_imdecode_on_android_paths() -> None:
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with (
        patch("modules.image_io.is_android", return_value=True),
        patch(
            "modules.image_io._decode_bgr_from_android_path", return_value=frame
        ) as mock_load,
    ):
        result = load_bgr_image("/data/user/0/app/cache/picked_image.jpg")

    mock_load.assert_called_once_with("/data/user/0/app/cache/picked_image.jpg")
    assert result is frame


def test_load_bgr_image_reads_content_uri_with_android_bitmap() -> None:
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with (
        patch("modules.image_io.is_android", return_value=True),
        patch(
            "modules.image_io._decode_bgr_from_android_uri", return_value=frame
        ) as mock_decode,
    ):
        result = load_bgr_image("content://media/external/images/media/1")

    mock_decode.assert_called_once_with("content://media/external/images/media/1")
    assert result is frame


def test_load_bgr_image_returns_none_when_uri_read_fails() -> None:
    with (
        patch("modules.image_io.is_android", return_value=True),
        patch("modules.image_io._read_uri_bytes", return_value=None),
    ):
        assert load_bgr_image("content://example/image") is None


def test_load_bgr_image_returns_none_when_imread_fails() -> None:
    with (
        patch("modules.image_io.is_android", return_value=False),
        patch("modules.image_io.cv2.imread", return_value=None),
    ):
        assert load_bgr_image("/tmp/missing.png") is None


def test_decode_bgr_from_bytes_reads_png() -> None:
    buffer = BytesIO()
    Image.new("RGB", (2, 3), color=(255, 0, 0)).save(buffer, format="PNG")
    payload = buffer.getvalue()

    image = _decode_bgr_from_bytes(payload, source="test.png")

    assert image is not None
    assert image.shape == (3, 2, 3)
    assert image[0, 0].tolist() == [0, 0, 255]


def test_decode_bgr_from_bytes_returns_none_for_invalid_bytes() -> None:
    assert _decode_bgr_from_bytes(b"not-an-image", source="bad.bin") is None
