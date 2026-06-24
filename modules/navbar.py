from __future__ import annotations

from collections.abc import Callable

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

_NAV_BG = (0.8, 0.8, 0.8, 0.7)
_NAV_BORDER = (0.6, 0.6, 0.6, 1)
_CAPTION_COLOR = (0.1, 0.1, 0.1, 1)
_PRESS_HIGHLIGHT = (1, 1, 1, 0.1)


class NavBarItem(ButtonBehavior, BoxLayout):
    def __init__(self, icon_source: str, label: str, **kwargs: object) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(2),
            padding=(0, dp(6), 0, dp(4)),
            size_hint_x=1,
            **kwargs,
        )
        self._pressed = False
        with self.canvas.before:
            self._press_color = Color(*_PRESS_HIGHLIGHT)
            self._press_rect = Rectangle(pos=self.pos, size=self.size)
        self._press_color.a = 0

        self.add_widget(
            Image(
                source=icon_source,
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                allow_stretch=True,
                keep_ratio=True,
                pos_hint={"center_x": 0.5},
            )
        )
        self.add_widget(
            Label(
                text=label,
                font_size="12sp",
                color=_CAPTION_COLOR,
                size_hint_y=None,
                height=dp(16),
            )
        )

        self.bind(pos=self._update_press_rect, size=self._update_press_rect)

    def _update_press_rect(self, *_args) -> None:
        self._press_rect.pos = self.pos
        self._press_rect.size = self.size

    def on_press(self) -> None:
        self._pressed = True
        self._press_color.a = _PRESS_HIGHLIGHT[3]

    def on_release(self) -> None:
        self._pressed = False
        self._press_color.a = 0


class BottomNavBar(BoxLayout):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=(dp(8), dp(4)),
            spacing=dp(4),
            **kwargs,
        )
        with self.canvas.before:
            Color(*_NAV_BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*_NAV_BORDER)
            self._border = Line(points=[0, 0, 0, 0], width=1)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, *_args) -> None:
        self._bg.pos = self.pos
        self._bg.size = self.size
        x, y = self.pos
        w = self.width
        top = y + self.height
        self._border.points = [x, top, x + w, top]

    def add_item(
        self,
        icon_source: str,
        label: str,
        on_press: Callable[[], None] | None = None,
    ) -> NavBarItem:
        item = NavBarItem(icon_source=icon_source, label=label)
        if on_press is not None:
            item.bind(on_press=lambda *_: on_press())
        self.add_widget(item)
        return item
