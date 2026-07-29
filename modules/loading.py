from __future__ import annotations

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget


class IndeterminateProgressBar(Widget):
    # 0..1 controlling how much of the bar is currently filled.
    fraction = NumericProperty(0.0)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._anim: Animation | None = None
        self._last_fraction = 0.0

        # Custom-draw both the track and the filled portion.
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)  # track/background
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            Color(0.4, 0.4, 0.4, 1)  # filled portion
            self._fg_rect = Rectangle(pos=self.pos, size=(0, self.height))

        self.bind(
            pos=self._update_rects, size=self._update_rects, fraction=self._update_rects
        )
        self._update_rects()

    def start(self) -> None:
        self.stop()
        self.fraction = 0.0

        # Fill left->right, then empty left->right (by right-anchoring during deplete).
        anim = Animation(fraction=1.0, duration=1.2, t="in_out_quad") + Animation(
            fraction=0.0, duration=1.2, t="in_out_quad"
        )
        anim.repeat = True
        anim.start(self)
        self._anim = anim
        self._update_rects()

    def stop(self) -> None:
        if self._anim is not None:
            self._anim.cancel(self)
            self._anim = None

    def _update_rects(self, *_: object) -> None:
        frac = max(0.0, min(1.0, float(self.fraction)))
        fw = self.width * frac

        # Direction-aware anchoring:
        # - filling (fraction increasing): anchor LEFT edge
        # - emptying (fraction decreasing): anchor RIGHT edge => empties left-to-right
        if frac >= self._last_fraction:
            x = self.x
        else:
            x = self.x + (self.width - fw)

        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        self._fg_rect.pos = (x, self.y)
        self._fg_rect.size = (fw, self.height)

        self._last_fraction = frac


def show_scanning_modal(message: str) -> ModalView:
    content = BoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(12),
        size_hint_y=None,
    )
    content.bind(minimum_height=content.setter("height"))
    content.add_widget(
        Label(
            text=message,
            font_size="18sp",
            size_hint_y=None,
            height=dp(28),
            halign="center",
        )
    )
    progress = IndeterminateProgressBar(size_hint_y=None, height=dp(6))
    content.add_widget(progress)

    modal = ModalView(
        size_hint=(0.8, None),
        height=dp(120),
        auto_dismiss=False,
    )
    modal.add_widget(content)
    modal.bind(on_dismiss=lambda *_: progress.stop())
    progress.start()
    modal.open()
    return modal
