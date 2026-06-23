from __future__ import annotations

from kivy.uix.screenmanager import ScreenManager
from modules.screens import CAMERA_SCREEN, FILE_SELECT_SCREEN, HOME_SCREEN

from main import MainApp


def test_main_app_build_returns_screen_manager() -> None:
    app = MainApp()
    root = app.build()
    assert isinstance(root, ScreenManager)


def test_switches_home_and_camera() -> None:
    app = MainApp()
    root = app.build()
    assert root.current == HOME_SCREEN

    app._open_camera()
    assert root.current == CAMERA_SCREEN

    app._show_home()
    assert root.current == HOME_SCREEN


def test_switches_home_and_file_select() -> None:
    app = MainApp()
    root = app.build()
    assert root.current == HOME_SCREEN

    app._open_file_select()
    assert root.current == FILE_SELECT_SCREEN

    app._show_home()
    assert root.current == HOME_SCREEN
