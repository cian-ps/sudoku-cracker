from __future__ import annotations

import os
import logging

from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config

from modules.home import Home

os.environ.setdefault("KIVY_NO_ARGS", "1")
logging.basicConfig(level=logging.DEBUG)

Config.set("graphics", "headless", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("kivy", "log_level", "info")
Config.write()

SOFTINPUT_MODE = "below_target"


class MainApp(App):
    def build(self) -> Home:
        Window.softinput_mode = SOFTINPUT_MODE
        return Home()


if __name__ == "__main__":
    MainApp().run()
