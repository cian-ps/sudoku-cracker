from __future__ import annotations

import numpy as np

from modules.camera_frames import (
    bgr_to_preview_texture,
    nv21_bytes_to_bgr,
    rotate_bgr,
)


def test_bgr_to_preview_texture_desktop_size() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    texture = bgr_to_preview_texture(frame, android=False)
    assert texture.size == (640, 480)
    assert texture.colorfmt == "bgr"


def test_bgr_to_preview_texture_android_size() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    texture = bgr_to_preview_texture(frame, android=True)
    assert texture.size == (640, 480)
    assert texture.colorfmt == "rgb"


def test_nv21_bytes_to_bgr_shape() -> None:
    width, height = 4, 4
    buffer = bytes([128] * (width * height * 3 // 2))
    frame = nv21_bytes_to_bgr(buffer, width, height)
    assert frame.shape == (height, width, 3)


def test_rotate_bgr_90_changes_shape() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    rotated = rotate_bgr(frame, 90)
    assert rotated.shape == (640, 480, 3)


def test_rotate_bgr_0_is_unchanged() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert rotate_bgr(frame, 0) is frame
