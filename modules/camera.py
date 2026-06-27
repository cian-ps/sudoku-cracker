from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

import cv2
import numpy as np
from kivy.clock import Clock
from kivy.core.camera import Camera as CoreCamera
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView

from modules.camera_frames import (
    bgr_to_preview_texture,
    get_android_camera_rotation,
    nv21_bytes_to_bgr,
    rotate_bgr,
)
from modules.image_parsing import (
    extract_grid,
    draw_contour,
    InferenceEngine,
    ObjectDetectionError,
    OCREngineError,
    OCRMismatchError,
)
from modules.loading import show_scanning_modal
from modules.messages import (
    CAMERA_FRAME_ERROR_TEXT,
    CAMERA_NO_FRAME_TEXT,
    CAMERA_UNAVAILABLE_TEXT,
    GRID_NOT_FOUND_TEXT,
    OCR_MISMATCH_TEXT,
    OCR_UNAVAILABLE_TEXT,
    SCAN_FAILED_TEXT,
    SCANNING_TEXT,
)
from modules.ocr.model_assets import is_android

_CAMERA_TRANSIENT_STATUS_TEXTS = frozenset(
    {
        CAMERA_FRAME_ERROR_TEXT,
        CAMERA_NO_FRAME_TEXT,
    }
)

_CAMERA_SCAN_ERROR_TEXTS = frozenset(
    {
        GRID_NOT_FOUND_TEXT,
        OCR_MISMATCH_TEXT,
        OCR_UNAVAILABLE_TEXT,
        SCAN_FAILED_TEXT,
    }
)

_FRAME_INTERVAL = 1.0 / 30.0
_ANDROID_CAMERA_RESOLUTION = (640, 480)


def _has_camera_permission() -> bool:
    try:
        from android.permissions import Permission, check_permission
    except ImportError:
        return True
    return bool(check_permission(Permission.CAMERA))


def _request_camera_permission(
    callback: Callable[[list[str], list[bool]], None],
) -> None:
    try:
        from android.permissions import Permission, request_permissions
    except ImportError:
        callback([], [True])
        return
    request_permissions([Permission.CAMERA], callback)


class Camera(BoxLayout):
    def __init__(
        self,
        on_capture: Callable[[np.ndarray], None],
        on_cancel: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical", padding=dp(10), spacing=dp(10), **kwargs
        )
        self._on_capture = on_capture
        self._on_cancel = on_cancel
        self._frame: np.ndarray | None = None
        self._vidcap: cv2.VideoCapture | None = None
        self._android_camera: Any | None = None
        self._android_rotation = 90
        self._update_event = None
        self._scanning = False
        self._scan_cancelled = False
        self._scan_modal: ModalView | None = None

        self._preview = Image(size_hint=(1, 1), fit_mode="cover")
        self._status = Label(
            text="",
            font_size="20sp",
            size_hint_y=None,
            height=dp(24),
            color=(0.8, 0.2, 0.2, 1),
        )

        button_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
        )
        self._back_btn = Button(text="Back", font_size="20sp")
        self._scan_btn = Button(
            text="Scan",
            font_size="20sp",
            background_color=(0.2, 0.8, 1, 1),
        )
        self._back_btn.bind(on_press=self._handle_back)
        self._scan_btn.bind(on_press=self._handle_scan)

        button_row.add_widget(self._back_btn)
        button_row.add_widget(self._scan_btn)

        self.add_widget(self._preview)
        self.add_widget(self._status)
        self.add_widget(button_row)

    def on_enter(self) -> None:
        self._status.text = ""
        self._frame = None
        self._scanning = False
        self._scan_cancelled = False
        self._scan_modal = None

        if is_android():
            self._start_android_camera()
            return

        self._vidcap = cv2.VideoCapture(0)
        if not self._vidcap.isOpened():
            logging.error("VideoCapture(0) failed to open camera")
            self._status.text = CAMERA_UNAVAILABLE_TEXT
            self._scan_btn.disabled = True
            return

        self._scan_btn.disabled = False
        self._update_event = Clock.schedule_interval(self._update, _FRAME_INTERVAL)

    def _start_android_camera(self) -> None:
        if _has_camera_permission():
            self._open_android_core_camera()
            return

        def on_permission_result(
            _permissions: list[str], grant_results: list[bool]
        ) -> None:
            Clock.schedule_once(
                lambda _dt: self._on_camera_permission_result(grant_results),
                0,
            )

        _request_camera_permission(on_permission_result)

    def _on_camera_permission_result(self, grant_results: list[bool]) -> None:
        if self._scan_cancelled or self._android_camera is not None:
            return
        if grant_results and all(grant_results):
            self._open_android_core_camera()
            return

        logging.error("Camera permission denied")
        self._status.text = CAMERA_UNAVAILABLE_TEXT
        self._scan_btn.disabled = True

    def _open_android_core_camera(self) -> None:
        try:
            self._android_camera = CoreCamera(
                index=0,
                resolution=_ANDROID_CAMERA_RESOLUTION,
                stopped=True,
            )
            self._android_camera.start()
            self._android_rotation = get_android_camera_rotation(0)
        except Exception:
            logging.exception("CoreCamera failed to start")
            self._android_camera = None
            self._status.text = CAMERA_UNAVAILABLE_TEXT
            self._scan_btn.disabled = True
            return

        self._scan_btn.disabled = False
        self._update_event = Clock.schedule_interval(self._update, _FRAME_INTERVAL)

    def on_leave(self) -> None:
        self._scan_cancelled = True
        self._dismiss_scan_modal()
        self._scanning = False
        if self._update_event is not None:
            Clock.unschedule(self._update_event)
            self._update_event = None
        if self._vidcap is not None:
            self._vidcap.release()
            self._vidcap = None
        if self._android_camera is not None:
            self._android_camera.stop()
            self._android_camera = None
        self._frame = None

    def _update(self, *_args: object) -> None:
        if self._scanning:
            return

        if is_android():
            self._update_android()
        else:
            self._update_desktop()

    def _update_desktop(self) -> None:
        if self._vidcap is None:
            return

        ret, frame = self._vidcap.read()
        if not ret:
            logging.warning("VideoCapture.read() failed")
            self._frame = None
            self._status.text = CAMERA_FRAME_ERROR_TEXT
            self._scan_btn.disabled = True
            return

        self._apply_frame(frame, android=False)

    def _update_android(self) -> None:
        if self._android_camera is None:
            return

        buffer = self._android_camera.grab_frame()
        if buffer is None:
            return

        width, height = self._android_camera.resolution
        frame = nv21_bytes_to_bgr(buffer, width, height)
        frame = rotate_bgr(frame, self._android_rotation)
        self._apply_frame(frame, android=True)

    def _apply_frame(self, frame: np.ndarray, *, android: bool) -> None:
        self._frame = frame.copy()
        if self._status.text in _CAMERA_TRANSIENT_STATUS_TEXTS:
            self._status.text = ""
        self._scan_btn.disabled = False

        draw_contour(frame)
        self._preview.texture = bgr_to_preview_texture(frame, android=android)

    def _handle_back(self, *_args: object) -> None:
        self._on_cancel()

    def _dismiss_scan_modal(self) -> None:
        if self._scan_modal is not None:
            self._scan_modal.dismiss()
            self._scan_modal = None

    def _set_scan_ui_active(self, active: bool) -> None:
        self._scanning = active
        self._back_btn.disabled = active
        self._scan_btn.disabled = active

    def _run_scan(self, frame: np.ndarray) -> None:
        try:
            grid = extract_grid(frame)
            preds_array = InferenceEngine().run(grid)
        except ObjectDetectionError as e:
            logging.error(e)
            Clock.schedule_once(
                lambda _dt, msg=GRID_NOT_FOUND_TEXT: self._finish_scan_error(msg),
                0,
            )
            return
        except OCRMismatchError as e:
            logging.error(e)
            Clock.schedule_once(
                lambda _dt, msg=OCR_MISMATCH_TEXT: self._finish_scan_error(msg),
                0,
            )
            return
        except OCREngineError as e:
            logging.error(e)
            Clock.schedule_once(
                lambda _dt, msg=OCR_UNAVAILABLE_TEXT: self._finish_scan_error(msg),
                0,
            )
            return
        except Exception as e:
            logging.error(e)
            Clock.schedule_once(
                lambda _dt, msg=SCAN_FAILED_TEXT: self._finish_scan_error(msg),
                0,
            )
            return

        Clock.schedule_once(
            lambda _dt, preds=preds_array: self._finish_scan_success(preds),
            0,
        )

    def _finish_scan_success(self, preds_array: np.ndarray, *_args: object) -> None:
        if self._scan_cancelled:
            return

        self._dismiss_scan_modal()
        self._set_scan_ui_active(False)
        self._on_capture(preds_array)

    def _finish_scan_error(self, message: str, *_args: object) -> None:
        if self._scan_cancelled:
            return

        self._dismiss_scan_modal()
        self._set_scan_ui_active(False)
        self._status.text = message

    def _handle_scan(self, *_args: object) -> None:
        if self._scanning:
            return

        if self._status.text in _CAMERA_SCAN_ERROR_TEXTS:
            self._status.text = ""

        if self._frame is None:
            logging.warning("Scan pressed with no camera frame available")
            self._status.text = CAMERA_NO_FRAME_TEXT
            self._scan_btn.disabled = True
            return

        frame = self._frame.copy()
        self._set_scan_ui_active(True)
        self._scan_modal = show_scanning_modal(SCANNING_TEXT)

        thread = threading.Thread(target=self._run_scan, args=(frame,), daemon=True)
        thread.start()
