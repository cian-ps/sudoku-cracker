from __future__ import annotations

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar


class IndeterminateProgressBar(ProgressBar):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(max=100, value=0, **kwargs)
        self._anim: Animation | None = None

    def start(self) -> None:
        self.stop()
        anim = Animation(value=100, duration=1.2, t="in_out_quad") + Animation(
            value=0, duration=1.2, t="in_out_quad"
        )
        anim.repeat = True
        anim.start(self)
        self._anim = anim

    def stop(self) -> None:
        if self._anim is not None:
            self._anim.cancel(self)
            self._anim = None


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
