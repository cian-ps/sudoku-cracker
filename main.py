from __future__ import annotations

import logging
import os

import numpy as np
from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager

from modules.camera import Camera
from modules.home import Home
from modules.screens import CAMERA_SCREEN, HOME_SCREEN, build_screen_manager

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
logging.basicConfig(level=logging.DEBUG)

Config.set("graphics", "headless", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("kivy", "log_level", "info")
Config.write()

SOFTINPUT_MODE = "below_target"


class MainApp(App):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._home = Home(on_camera=self._open_camera)
        self._camera = Camera(
            on_capture=self._on_capture,
            on_cancel=self._show_home,
        )
        self._sm = build_screen_manager(self._home, self._camera)

    def build(self) -> ScreenManager:
        Window.softinput_mode = SOFTINPUT_MODE
        return self._sm

    def _open_camera(self) -> None:
        self._sm.current = CAMERA_SCREEN

    def _show_home(self) -> None:
        self._sm.current = HOME_SCREEN

    def _on_capture(self, ocr_result: np.ndarray) -> None:
        self._home.apply_board(ocr_result)
        self._show_home()


if __name__ == "__main__":
    MainApp().run()
