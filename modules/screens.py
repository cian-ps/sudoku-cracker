from __future__ import annotations

from kivy.uix.screenmanager import Screen, ScreenManager

from modules.camera import Camera
from modules.file_select import FileSelect
from modules.home import Home

HOME_SCREEN = "home"
CAMERA_SCREEN = "camera"
FILE_SELECT_SCREEN = "file_select"


class HomeScreen(Screen):
    def __init__(self, home: Home, **kwargs: object) -> None:
        super().__init__(name=HOME_SCREEN, **kwargs)
        self.home = home
        self.add_widget(home)


class CameraScreen(Screen):
    def __init__(self, camera: Camera, **kwargs: object) -> None:
        super().__init__(name=CAMERA_SCREEN, **kwargs)
        self._camera = camera
        self.add_widget(camera)

    def on_enter(self, *_args: object) -> None:
        super().on_enter(*_args)
        self._camera.on_enter()

    def on_leave(self, *_args: object) -> None:
        self._camera.on_leave()
        super().on_leave(*_args)


class FileSelectScreen(Screen):
    def __init__(self, file_select: FileSelect, **kwargs: object) -> None:
        super().__init__(name=FILE_SELECT_SCREEN, **kwargs)
        self._file_select = file_select
        self.add_widget(file_select)

    def on_enter(self, *_args: object) -> None:
        super().on_enter(*_args)
        self._file_select.on_enter()

    def on_leave(self, *_args: object) -> None:
        self._file_select.on_leave()
        super().on_leave(*_args)


def build_screen_manager(
    home: Home, camera: Camera, file_select: FileSelect
) -> ScreenManager:
    manager = ScreenManager()
    manager.add_widget(HomeScreen(home))
    manager.add_widget(CameraScreen(camera))
    manager.add_widget(FileSelectScreen(file_select))
    return manager
