from __future__ import annotations

import logging
from collections.abc import Callable

import cv2
import numpy as np
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label

from modules.messages import (
    CAMERA_FRAME_ERROR_TEXT,
    CAMERA_NO_FRAME_TEXT,
    CAMERA_UNAVAILABLE_TEXT,
)

_FRAME_INTERVAL = 1.0 / 30.0


class Camera(BoxLayout):
    def __init__(
        self,
        on_capture: Callable[[], None],
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
        self._update_event = None

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
        self._scan_btn = Button(text="Scan", font_size="20sp")
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
        self._vidcap = cv2.VideoCapture(0)
        if not self._vidcap.isOpened():
            logging.error("VideoCapture(0) failed to open camera")
            self._status.text = CAMERA_UNAVAILABLE_TEXT
            self._scan_btn.disabled = True
            return

        self._scan_btn.disabled = False
        self._update_event = Clock.schedule_interval(self._update, _FRAME_INTERVAL)

    def on_leave(self) -> None:
        if self._update_event is not None:
            Clock.unschedule(self._update_event)
            self._update_event = None
        if self._vidcap is not None:
            self._vidcap.release()
            self._vidcap = None
        self._frame = None

    def _update(self, *_args: object) -> None:
        if self._vidcap is None:
            return

        ret, frame = self._vidcap.read()
        if not ret:
            logging.warning("VideoCapture.read() failed")
            self._frame = None
            self._status.text = CAMERA_FRAME_ERROR_TEXT
            self._scan_btn.disabled = True
            return

        self._frame = frame
        if self._status.text in {
            CAMERA_FRAME_ERROR_TEXT,
            CAMERA_NO_FRAME_TEXT,
        }:
            self._status.text = ""
        self._scan_btn.disabled = False

        buffer = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
        self._preview.texture = texture

    def _handle_back(self, *_args: object) -> None:
        self._on_cancel()

    def _handle_scan(self, *_args: object) -> None:
        if self._frame is None:
            logging.warning("Scan pressed with no camera frame available")
            self._status.text = CAMERA_NO_FRAME_TEXT
            self._scan_btn.disabled = True
            return

        self._on_capture()
