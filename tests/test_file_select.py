from __future__ import annotations

from collections.abc import Callable, Sequence
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from modules.file_select import FileSelect
from modules.image_parsing import ObjectDetectionError, OCREngineError, OCRMismatchError
from modules.messages import (
    FILE_LOAD_FAILED_TEXT,
    FILE_NONE_SELECTED_TEXT,
    FILE_NO_IMAGE_TEXT,
    GRID_NOT_FOUND_TEXT,
    OCR_MISMATCH_TEXT,
    OCR_UNAVAILABLE_TEXT,
    SCAN_FAILED_TEXT,
)


def _dummy_frame() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def _run_continue_synchronously(file_select: FileSelect) -> None:
    with (
        patch(
            "modules.file_select.Clock.schedule_once",
            side_effect=lambda callback, _delay: callback(0),
        ),
        patch("modules.file_select.threading.Thread") as mock_thread,
    ):
        mock_thread.side_effect = lambda target, args=(), daemon=None: SimpleNamespace(
            start=lambda: target(*args)
        )
        file_select._handle_continue()


def _mock_filechooser(
    paths: Sequence[str],
) -> Callable[..., None]:
    def open_file(
        *, on_selection: Callable[[Sequence[str]], None], **_kwargs: object
    ) -> None:
        on_selection(paths)

    return open_file


def test_back_calls_on_cancel() -> None:
    cancelled = {"value": False}
    file_select = FileSelect(
        on_capture=lambda _: None, on_cancel=lambda: cancelled.update(value=True)
    )
    file_select._handle_back()
    assert cancelled["value"] is True


def test_on_enter_empty_selection_shows_message() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    with (
        patch(
            "modules.file_select.filechooser.open_file",
            side_effect=_mock_filechooser([]),
        ),
        patch(
            "modules.file_select.Clock.schedule_once",
            side_effect=lambda callback, _delay: callback(0),
        ),
    ):
        file_select.on_enter()

    assert file_select._status.text == FILE_NONE_SELECTED_TEXT
    assert file_select._continue_btn.disabled is True


def test_on_enter_loads_selected_image() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    frame = _dummy_frame()
    with (
        patch(
            "modules.file_select.filechooser.open_file",
            side_effect=_mock_filechooser(["/tmp/puzzle.png"]),
        ),
        patch("modules.file_select.cv2.imread", return_value=frame),
        patch(
            "modules.file_select.Clock.schedule_once",
            side_effect=lambda callback, _delay: callback(0),
        ),
    ):
        file_select.on_enter()

    assert file_select._status.text == ""
    assert file_select._image is not None
    assert file_select._continue_btn.disabled is False
    assert file_select._preview.texture is not None


def test_on_enter_load_failure_shows_message() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    with (
        patch(
            "modules.file_select.filechooser.open_file",
            side_effect=_mock_filechooser(["/tmp/bad.png"]),
        ),
        patch("modules.file_select.cv2.imread", return_value=None),
        patch(
            "modules.file_select.Clock.schedule_once",
            side_effect=lambda callback, _delay: callback(0),
        ),
    ):
        file_select.on_enter()

    assert file_select._status.text == FILE_LOAD_FAILED_TEXT
    assert file_select._continue_btn.disabled is True


def test_continue_without_image_shows_error() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    file_select._image = None
    file_select._handle_continue()
    assert file_select._status.text == FILE_NO_IMAGE_TEXT
    assert file_select._continue_btn.disabled is True


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
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    file_select._image = _dummy_frame()

    with patch("modules.file_select.extract_grid", side_effect=side_effect):
        _run_continue_synchronously(file_select)

    assert file_select._status.text == expected_text
    assert file_select._continue_btn.disabled is False
    assert file_select._scan_modal is None


def test_scan_ocr_unavailable_shows_user_message() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    file_select._image = _dummy_frame()

    with (
        patch("modules.file_select.extract_grid", return_value=_dummy_frame()),
        patch(
            "modules.file_select.InferenceEngine",
            side_effect=OCREngineError("Failed to initialize OCR engine."),
        ),
    ):
        _run_continue_synchronously(file_select)

    assert file_select._status.text == OCR_UNAVAILABLE_TEXT


def test_scan_success_calls_on_capture() -> None:
    captured: dict[str, np.ndarray | None] = {"value": None}
    file_select = FileSelect(
        on_capture=lambda preds: captured.update(value=preds),
        on_cancel=lambda: None,
    )
    file_select._image = _dummy_frame()
    expected = np.arange(81, dtype=np.int64).reshape(9, 9)

    with (
        patch("modules.file_select.extract_grid", return_value=_dummy_frame()),
        patch("modules.file_select.InferenceEngine") as mock_engine,
    ):
        mock_engine.return_value.parse_to_numpy.return_value = expected
        _run_continue_synchronously(file_select)

    captured_value = captured["value"]
    assert captured_value is not None
    assert np.array_equal(captured_value, expected)
    assert file_select._scan_modal is None


def test_continue_disables_buttons_while_in_progress() -> None:
    file_select = FileSelect(on_capture=lambda _: None, on_cancel=lambda: None)
    file_select._image = _dummy_frame()
    started: dict[str, bool] = {"value": False}

    def block_scan(_frame: np.ndarray) -> None:
        started["value"] = True
        assert file_select._back_btn.disabled is True
        assert file_select._continue_btn.disabled is True
        assert file_select._scan_modal is not None

    with patch("modules.file_select.FileSelect._run_scan", side_effect=block_scan):
        with patch("modules.file_select.threading.Thread") as mock_thread:
            mock_thread.side_effect = lambda target, args=(), daemon=None: (
                SimpleNamespace(start=lambda: target(*args))
            )
            file_select._handle_continue()

    assert started["value"] is True


def test_on_leave_cancels_pending_scan_result() -> None:
    captured = {"value": False}
    file_select = FileSelect(
        on_capture=lambda _: captured.update(value=True),
        on_cancel=lambda: None,
    )
    file_select._image = _dummy_frame()
    file_select._scan_cancelled = False

    with patch("modules.file_select.FileSelect._run_scan"):
        with patch("modules.file_select.threading.Thread") as mock_thread:
            mock_thread.side_effect = lambda target, args=(), daemon=None: (
                SimpleNamespace(start=lambda: target(*args))
            )
            file_select._handle_continue()

    file_select.on_leave()
    file_select._finish_scan_success(np.zeros((9, 9), dtype=np.int64))

    assert captured["value"] is False
