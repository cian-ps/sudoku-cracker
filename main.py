from __future__ import annotations

import os
import numpy as np
import logging

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.config import Config

from modules.backtracking import SudokuBacktracking

os.environ.setdefault("KIVY_NO_ARGS", "1")
logging.basicConfig(level=logging.DEBUG)

Config.set("graphics", "headless", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("kivy", "log_level", "info")
Config.write()

ERROR_TEXT = "Invalid or unsolvable puzzle"


class Home(BoxLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            orientation="vertical", padding=dp(10), spacing=dp(10), **kwargs
        )
        self.cells: list[TextInput] = []
        self._build_ui()

    @staticmethod
    def _digit_filter(substring: str, from_undo: bool = False) -> str:
        if substring in "123456789":
            return substring
        return ""

    def _fit_cell_font(self, cell: TextInput, *_args) -> None:
        side = min(cell.width, cell.height)
        if side <= 0:
            return
        pad = max(1, side * 0.08)
        cell.padding = [pad, pad, pad, pad]
        inner = side - 2 * pad
        cell.font_size = max(8, inner * 0.75)

    def _create_cell(self) -> TextInput:
        cell = TextInput(
            multiline=False,
            halign="center",
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            background_normal="",
            background_active="",
            cursor_color=(0, 0, 0, 1),
            input_filter=self._digit_filter,
        )
        cell.bind(
            focus=self._on_cell_focus,
            text=self._on_cell_text,
            size=self._fit_cell_font,
        )
        return cell

    def _on_cell_focus(self, cell: TextInput, focused: bool) -> None:
        if focused and cell.text:
            cell.select_all()

    def _on_cell_text(self, cell: TextInput, value: str) -> None:
        if len(value) <= 1:
            return
        cell.unbind(text=self._on_cell_text)
        cell.text = value[-1] if value[-1] in "123456789" else ""
        cell.bind(text=self._on_cell_text)

    def _build_board(self) -> GridLayout:
        outer = GridLayout(rows=3, cols=3, spacing=dp(6))
        for _ in range(3):
            for _ in range(3):
                inner = GridLayout(rows=3, cols=3, spacing=dp(2))
                for _ in range(3):
                    for _ in range(3):
                        cell = self._create_cell()
                        self.cells.append(cell)
                        inner.add_widget(cell)
                outer.add_widget(inner)
        return outer

    def _keep_board_square(self, container: AnchorLayout, *_args) -> None:
        side = min(container.width, container.height)
        self.board.size = (side, side)

    def _build_ui(self) -> None:
        title = Image(
            source="assets/sudoku-cracker-banner.png",
            size_hint_y=0.3,
            height=dp(100),
        )
        self.status = Label(
            text="",
            font_size="20sp",
            size_hint_y=None,
            height=dp(24),
            color=(0.8, 0.2, 0.2, 1),
        )

        self.board = self._build_board()
        self.board.size_hint = (None, None)
        grid_area = AnchorLayout(size_hint=(1, 1))
        grid_area.add_widget(self.board)
        grid_area.bind(size=self._keep_board_square, pos=self._keep_board_square)

        button_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
        )
        clear_btn = Button(text="Clear", font_size="20sp")
        solve_btn = Button(
            text="Solve", font_size="20sp", background_color=(0.2, 0.8, 1, 1)
        )
        clear_btn.bind(on_press=self._on_clear)
        solve_btn.bind(on_press=self._on_solve)
        button_row.add_widget(clear_btn)
        button_row.add_widget(solve_btn)

        self.add_widget(title)
        self.add_widget(self.status)
        self.add_widget(grid_area)
        self.add_widget(button_row)

    @staticmethod
    def _cell_index(row: int, col: int) -> int:
        block_row, block_col = row // 3, col // 3
        inner_row, inner_col = row % 3, col % 3
        block_index = block_row * 3 + block_col
        within_block = inner_row * 3 + inner_col
        return block_index * 9 + within_block

    def _board_to_ndarray(self) -> np.ndarray:
        board = np.zeros((9, 9), dtype=np.int64)
        for row in range(9):
            for col in range(9):
                text = self.cells[self._cell_index(row, col)].text.strip()
                board[row, col] = int(text) if text else 0
        return board

    def _apply_solution(self, solution: np.ndarray) -> None:
        for row in range(9):
            for col in range(9):
                val = solution[row, col]
                self.cells[self._cell_index(row, col)].text = str(val) if val else ""

    def _on_clear(self, *_args) -> None:
        self.status.text = ""
        for cell in self.cells:
            cell.text = ""

    def _on_solve(self, *_args) -> None:
        self.status.text = ""
        board = self._board_to_ndarray()
        try:
            solution = SudokuBacktracking(board).get_solution()
            logging.debug(solution)
        except RecursionError:
            self.status.text = ERROR_TEXT
            return
        self._apply_solution(solution)


class MainApp(App):
    def build(self) -> Home:
        return Home()


if __name__ == "__main__":
    MainApp().run()
