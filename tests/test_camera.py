from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from modules.camera import Camera
from modules.messages import (
    CAMERA_FRAME_ERROR_TEXT,
    CAMERA_NO_FRAME_TEXT,
    CAMERA_UNAVAILABLE_TEXT,
    GRID_NOT_FOUND_TEXT,
    OCR_MISMATCH_TEXT,
    OCR_UNAVAILABLE_TEXT,
    SCAN_FAILED_TEXT,
)
from modules.image_parsing import ObjectDetectionError, OCREngineError, OCRMismatchError


def _dummy_frame() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def _run_scan_synchronously(camera: Camera) -> None:
    with (
        patch(
            "modules.camera.Clock.schedule_once",
            side_effect=lambda callback, _delay: callback(0),
        ),
        patch("modules.camera.threading.Thread") as mock_thread,
    ):
        mock_thread.side_effect = lambda target, args=(), daemon=None: SimpleNamespace(
            start=lambda: target(*args)
        )
        camera._handle_scan()


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


@pytest.mark.parametrize(
    ("side_effect", "expected_text"),
    [
        (ObjectDetectionError("no grid"), GRID_NOT_FOUND_TEXT),
        (OCRMismatchError("mismatch"), OCR_MISMATCH_TEXT),
        (RuntimeError("boom"), SCAN_FAILED_TEXT),
    ],
)
def test_scan_errors_show_user_message(
    side_effect: Exception, expected_text: str
) -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()

    with patch("modules.camera.extract_grid", side_effect=side_effect):
        _run_scan_synchronously(camera)

    assert camera._status.text == expected_text
    assert camera._scan_btn.disabled is False
    assert camera._scan_modal is None


def test_scan_ocr_unavailable_shows_user_message() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()

    with (
        patch("modules.camera.extract_grid", return_value=_dummy_frame()),
        patch(
            "modules.camera.InferenceEngine.run",
            side_effect=OCREngineError("Failed to initialize OCR engine."),
        ),
    ):
        _run_scan_synchronously(camera)

    assert camera._status.text == OCR_UNAVAILABLE_TEXT
    assert camera._scan_btn.disabled is False


def test_scan_success_calls_on_capture() -> None:
    captured: dict[str, np.ndarray | None] = {"value": None}
    camera = Camera(
        on_capture=lambda preds: captured.update(value=preds),
        on_cancel=lambda: None,
    )
    camera._frame = _dummy_frame()
    expected = np.arange(81, dtype=np.uint8).reshape(9, 9)

    with (
        patch("modules.camera.extract_grid", return_value=_dummy_frame()),
        patch("modules.camera.InferenceEngine.run", return_value=expected),
    ):
        _run_scan_synchronously(camera)

    captured_value = captured["value"]
    assert captured_value is not None
    assert np.array_equal(captured_value, expected)
    assert camera._scan_modal is None


def test_scan_disables_buttons_while_in_progress() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()
    started: dict[str, bool] = {"value": False}

    def block_scan(_frame: np.ndarray) -> None:
        started["value"] = True
        assert camera._back_btn.disabled is True
        assert camera._scan_btn.disabled is True
        assert camera._scan_modal is not None

    with patch("modules.camera.Camera._run_scan", side_effect=block_scan):
        with patch("modules.camera.threading.Thread") as mock_thread:
            mock_thread.side_effect = lambda target, args=(), daemon=None: (
                SimpleNamespace(start=lambda: target(*args))
            )
            camera._handle_scan()

    assert started["value"] is True


def test_scan_error_persists_across_camera_frames() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()
    fake: object = _FakeCapture()
    camera._vidcap = fake  # type: ignore[assignment]

    with patch(
        "modules.camera.extract_grid", side_effect=ObjectDetectionError("no grid")
    ):
        _run_scan_synchronously(camera)

    assert camera._status.text == GRID_NOT_FOUND_TEXT
    with patch("modules.camera.draw_contour"):
        camera._update()
    assert camera._status.text == GRID_NOT_FOUND_TEXT


def test_scan_error_cleared_on_retry() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()
    camera._status.text = GRID_NOT_FOUND_TEXT

    with patch("modules.camera.Camera._run_scan"):
        with patch("modules.camera.threading.Thread") as mock_thread:
            mock_thread.side_effect = lambda target, args=(), daemon=None: (
                SimpleNamespace(start=lambda: target(*args))
            )
            camera._handle_scan()

    assert camera._status.text == ""


def test_scan_ignored_while_already_scanning() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._frame = _dummy_frame()
    camera._scanning = True
    camera._status.text = "existing"

    camera._handle_scan()

    assert camera._status.text == "existing"


def test_transient_error_cleared_on_good_frame() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    fake: object = _FakeCapture()
    camera._vidcap = fake  # type: ignore[assignment]
    camera._status.text = CAMERA_FRAME_ERROR_TEXT

    with patch("modules.camera.draw_contour"):
        camera._update()

    assert camera._status.text == ""
    assert camera._scan_btn.disabled is False


def test_update_skipped_while_scanning() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    fake: object = _FakeCapture()
    camera._vidcap = fake  # type: ignore[assignment]
    camera._scanning = True
    camera._frame = None

    with patch("modules.camera.draw_contour") as draw_contour:
        camera._update()
        draw_contour.assert_not_called()

    assert camera._frame is None


def test_on_enter_schedules_camera_updates() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)

    with (
        patch("modules.camera.cv2.VideoCapture", return_value=_FakeCapture()),
        patch("modules.camera.Clock.schedule_interval") as schedule_interval,
    ):
        camera.on_enter()

    schedule_interval.assert_called_once()
    assert camera._update_event is schedule_interval.return_value


def test_on_leave_cancels_pending_scan_result() -> None:
    captured = {"value": False}
    camera = Camera(
        on_capture=lambda _: captured.update(value=True),
        on_cancel=lambda: None,
    )
    camera._frame = _dummy_frame()
    camera._scan_cancelled = False

    with patch("modules.camera.Camera._run_scan"):
        with patch("modules.camera.threading.Thread") as mock_thread:
            mock_thread.side_effect = lambda target, args=(), daemon=None: (
                SimpleNamespace(start=lambda: target(*args))
            )
            camera._handle_scan()

    camera.on_leave()
    camera._finish_scan_success(np.zeros((9, 9), dtype=np.uint8))

    assert captured["value"] is False


def test_finish_scan_error_ignored_when_cancelled() -> None:
    camera = Camera(on_capture=lambda _: None, on_cancel=lambda: None)
    camera._scan_cancelled = True

    camera._finish_scan_error(SCAN_FAILED_TEXT)

    assert camera._status.text == ""
