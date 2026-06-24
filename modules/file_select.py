from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Sequence

import cv2
import numpy as np
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar
from plyer import filechooser

from modules.image_parsing import (
    InferenceEngine,
    ObjectDetectionError,
    OCREngineError,
    OCRMismatchError,
    extract_grid,
)
from modules.messages import (
    FILE_LOAD_FAILED_TEXT,
    FILE_NONE_SELECTED_TEXT,
    FILE_NO_IMAGE_TEXT,
    GRID_NOT_FOUND_TEXT,
    OCR_MISMATCH_TEXT,
    OCR_UNAVAILABLE_TEXT,
    SCAN_FAILED_TEXT,
    SCANNING_TEXT,
)

_FILE_SCAN_ERROR_TEXTS = frozenset(
    {
        GRID_NOT_FOUND_TEXT,
        OCR_MISMATCH_TEXT,
        OCR_UNAVAILABLE_TEXT,
        SCAN_FAILED_TEXT,
    }
)

_IMAGE_FILTER = [["Images", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]]


class FileSelect(BoxLayout):
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
        self._image: np.ndarray | None = None
        self._file_path: str | None = None
        self._scanning = False
        self._scan_cancelled = False
        self._scan_modal: ModalView | None = None

        self._preview = Image(size_hint=(1, 1))
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
        self._continue_btn = Button(text="Continue", font_size="20sp")
        self._back_btn.bind(on_press=self._handle_back)
        self._continue_btn.bind(on_press=self._handle_continue)

        button_row.add_widget(self._back_btn)
        button_row.add_widget(self._continue_btn)

        self.add_widget(self._preview)
        self.add_widget(self._status)
        self.add_widget(button_row)

    def on_enter(self) -> None:
        self._status.text = ""
        self._image = None
        self._file_path = None
        self._scanning = False
        self._scan_cancelled = False
        self._scan_modal = None
        self._continue_btn.disabled = True
        self._clear_preview()
        filechooser.open_file(
            on_selection=self._on_file_chosen,
            filters=_IMAGE_FILTER,
        )

    def on_leave(self) -> None:
        self._scan_cancelled = True
        self._dismiss_scan_modal()
        self._scanning = False
        self._image = None
        self._file_path = None
        self._clear_preview()

    def _on_file_chosen(self, paths: Sequence[str]) -> None:
        Clock.schedule_once(lambda _dt: self._handle_file_selection(paths), 0)

    def _handle_file_selection(self, paths: Sequence[str]) -> None:
        if self._scan_cancelled:
            return

        if not paths:
            logging.warning("File selection cancelled or empty")
            self._status.text = FILE_NONE_SELECTED_TEXT
            self._image = None
            self._file_path = None
            self._clear_preview()
            self._continue_btn.disabled = True
            return

        path = paths[0]
        image = cv2.imread(path)
        if image is None:
            logging.error("cv2.imread failed for %s", path)
            self._status.text = FILE_LOAD_FAILED_TEXT
            self._image = None
            self._file_path = None
            self._clear_preview()
            self._continue_btn.disabled = True
            return

        self._status.text = ""
        self._image = image
        self._file_path = path
        self._update_preview(image)
        self._continue_btn.disabled = False

    def _clear_preview(self) -> None:
        self._preview.texture = None

    def _update_preview(self, image: np.ndarray) -> None:
        buffer = cv2.flip(image, 0).tobytes()
        texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
        self._preview.texture = texture

    def _handle_back(self, *_args: object) -> None:
        self._on_cancel()

    def _show_scan_modal(self) -> ModalView:
        content = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        content.add_widget(
            Label(
                text=SCANNING_TEXT,
                font_size="18sp",
                size_hint_y=None,
                height=dp(28),
                halign="center",
            )
        )
        content.add_widget(ProgressBar(max=0, size_hint_y=None, height=dp(4)))

        modal = ModalView(
            size_hint=(0.8, None),
            height=dp(120),
            auto_dismiss=False,
        )
        modal.add_widget(content)
        modal.open()
        return modal

    def _dismiss_scan_modal(self) -> None:
        if self._scan_modal is not None:
            self._scan_modal.dismiss()
            self._scan_modal = None

    def _set_scan_ui_active(self, active: bool) -> None:
        self._scanning = active
        self._back_btn.disabled = active
        self._continue_btn.disabled = active

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
        if self._image is not None:
            self._continue_btn.disabled = False

    def _handle_continue(self, *_args: object) -> None:
        if self._scanning:
            return

        if self._status.text in _FILE_SCAN_ERROR_TEXTS:
            self._status.text = ""

        if self._image is None:
            logging.warning("Continue pressed with no image available")
            self._status.text = FILE_NO_IMAGE_TEXT
            self._continue_btn.disabled = True
            return

        frame = self._image.copy()
        self._set_scan_ui_active(True)
        self._scan_modal = self._show_scan_modal()

        thread = threading.Thread(target=self._run_scan, args=(frame,), daemon=True)
        thread.start()
