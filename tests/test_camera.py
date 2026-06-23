from __future__ import annotations

from unittest.mock import patch

import numpy as np

from modules.camera import Camera
from modules.messages import (
    CAMERA_FRAME_ERROR_TEXT,
    CAMERA_NO_FRAME_TEXT,
    CAMERA_UNAVAILABLE_TEXT,
)


def _dummy_frame() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


class _FakeCapture:
    def __init__(self, *, opened: bool = True, readable: bool = True) -> None:
        self._opened = opened
        self._readable = readable
        self.released = False

    def isOpened(self) -> bool:
        return self._opened

    def read(self) -> tuple[bool, np.ndarray]:
        if not self._readable:
            return False, _dummy_frame()
        return True, _dummy_frame()

    def release(self) -> None:
        self.released = True


def test_back_calls_on_cancel() -> None:
    cancelled = {"value": False}
    camera = Camera(
        on_capture=lambda _: None, on_cancel=lambda: cancelled.update(value=True)
    )
    camera._handle_back()
    assert cancelled["value"] is True


def test_on_enter_shows_unavailable_when_camera_fails() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    with patch(
        "modules.camera.cv2.VideoCapture", return_value=_FakeCapture(opened=False)
    ):
        camera.on_enter()

    assert camera._status.text == CAMERA_UNAVAILABLE_TEXT
    assert camera._scan_btn.disabled is True


def test_scan_without_frame_shows_error() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = None
    camera._handle_scan()
    assert camera._status.text == CAMERA_NO_FRAME_TEXT
    assert camera._scan_btn.disabled is True


def test_read_failure_disables_scan() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    fake: object = _FakeCapture(readable=False)
    camera._vidcap = fake  # type: ignore[assignment]
    camera._update()

    assert camera._status.text == CAMERA_FRAME_ERROR_TEXT
    assert camera._scan_btn.disabled is True


def test_on_leave_releases_capture_and_unschedules() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)

    with patch(
        "modules.camera.cv2.VideoCapture", return_value=_FakeCapture()
    ) as capture_cls:
        camera.on_enter()
        fake = capture_cls.return_value

    with patch("modules.camera.Clock.unschedule") as unschedule:
        camera.on_leave()
        unschedule.assert_called_once()

    assert fake.released is True
