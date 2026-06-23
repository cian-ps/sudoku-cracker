import numpy as np
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput

from modules.home import Home
from modules.backtracking import BacktrackingError
from modules.messages import (
    INVALID_PUZZLE_TEXT,
    UNSOLVABLE_PUZZLE_TEXT,
)


def _visual_cell(home, row, col):
    """Return the TextInput widget at the on-screen (row, col) position."""
    block_row, block_col = row // 3, col // 3
    inner_row, inner_col = row % 3, col % 3
    blocks = list(reversed(home.board.children))
    block = blocks[block_row * 3 + block_col]
    cells_in_block = list(reversed(block.children))
    return cells_in_block[inner_row * 3 + inner_col]


def _fill_visual_board(home, board):
    for row in range(9):
        for col in range(9):
            val = board[row, col]
            if val:
                _visual_cell(home, row, col).text = str(val)


def test_digit_filter_accepts_one_through_nine():
    for i in range(1, 10):
        assert Home._digit_filter(str(i)) == str(i)


def test_digit_filter_rejects_zero_and_non_digits():
    assert Home._digit_filter("0") == ""
    assert Home._digit_filter("a") == ""


def test_home_creates_81_cells(home):
    assert len(home.cells) == 81


def test_home_cells_are_text_inputs(home):
    assert all(isinstance(cell, TextInput) for cell in home.cells)


def test_cells_use_number_input_type(home):
    assert all(cell.input_type == "number" for cell in home.cells)


def test_main_app_sets_below_target_softinput_mode():
    from kivy.core.window import Window

    from main import MainApp
    from main import SOFTINPUT_MODE

    MainApp().build()
    assert Window.softinput_mode == SOFTINPUT_MODE


def test_cell_font_scales_with_size(home):
    cell = home.cells[0]
    cell.size = (30, 30)
    home._fit_cell_font(cell)
    small_font = cell.font_size
    assert small_font > 0
    assert small_font < 30
    assert cell.padding[0] < 6

    cell.size = (100, 100)
    home._fit_cell_font(cell)
    assert cell.font_size > small_font


def test_on_cell_text_keeps_single_digit(home):
    cell = home.cells[0]
    cell.text = "5"
    home._on_cell_text(cell, "5")
    assert cell.text == "5"


def test_on_cell_text_keeps_last_valid_digit(home):
    cell = home.cells[0]
    cell.text = "4"
    home._on_cell_text(cell, "47")
    assert cell.text == "7"


def test_on_cell_text_clears_invalid_multi_char(home):
    cell = home.cells[0]
    cell.text = "3"
    home._on_cell_text(cell, "3a")
    assert cell.text == ""


def test_is_puzzle_valid_accepts_example(example):
    assert Home._is_puzzle_valid(example)


def test_is_puzzle_valid_rejects_duplicate_in_row(example):
    puzzle = example.copy()
    puzzle[0, 1] = 4
    assert not Home._is_puzzle_valid(puzzle)


def test_board_to_ndarray_empty(home):
    board = home._board_to_ndarray()
    assert board.shape == (9, 9)
    assert board.dtype == np.uint8
    assert np.all(board == 0)


def test_board_to_ndarray_reads_row_major(home):
    _visual_cell(home, 0, 0).text = "5"
    _visual_cell(home, 1, 2).text = "9"
    _visual_cell(home, 8, 8).text = "1"

    board = home._board_to_ndarray()
    assert board[0, 0] == 5
    assert board[1, 2] == 9
    assert board[8, 8] == 1


def test_on_clear_empties_all_cells(home):
    _visual_cell(home, 0, 0).text = "1"
    _visual_cell(home, 4, 4).text = "5"
    _visual_cell(home, 8, 8).text = "9"

    home._on_clear()

    assert all(cell.text == "" for cell in home.cells)


def test_on_clear_resets_status(home):
    home.status.text = INVALID_PUZZLE_TEXT
    home._on_clear()
    assert home.status.text == ""


def test_on_solve_example(home, example, example_solution):
    _fill_visual_board(home, example)
    home._on_solve()

    for row in range(9):
        for col in range(9):
            assert _visual_cell(home, row, col).text == str(example_solution[row, col])


def test_on_solve_invalid_example_sets_status(home, example):
    puzzle = example.copy()
    puzzle[0, 1] = 4
    _fill_visual_board(home, puzzle)
    home._on_solve()

    assert home.status.text == INVALID_PUZZLE_TEXT
    assert _visual_cell(home, 0, 0).text == "4"
    assert _visual_cell(home, 0, 1).text == "4"
    assert _visual_cell(home, 0, 3).text == "6"


def test_on_solve_unsolvable_sets_status(home, example, monkeypatch):
    _fill_visual_board(home, example)

    class FailingSolver:
        def __init__(self, _board):
            pass

        def get_solution(self):
            raise RecursionError("attempted 1001 of 1000 maximum allowed recursions")

    monkeypatch.setattr("modules.home.SudokuBacktracking", FailingSolver)
    home._on_solve()

    assert home.status.text == UNSOLVABLE_PUZZLE_TEXT
    assert _visual_cell(home, 0, 0).text == "4"
    assert _visual_cell(home, 0, 3).text == "6"


def test_on_solve_backtracking_error_sets_status(home, example, monkeypatch):
    _fill_visual_board(home, example)

    class FailingSolver:
        def __init__(self, _board):
            pass

        def get_solution(self):
            raise BacktrackingError("Backtracking algorithm failed to find a solution.")

    monkeypatch.setattr("modules.home.SudokuBacktracking", FailingSolver)
    home._on_solve()

    assert home.status.text == UNSOLVABLE_PUZZLE_TEXT
    assert _visual_cell(home, 0, 0).text == "4"


def test_on_solve_unexpected_error_sets_status(home, example, monkeypatch):
    _fill_visual_board(home, example)

    class FailingSolver:
        def __init__(self, _board):
            pass

        def get_solution(self):
            raise RuntimeError("unexpected failure")

    monkeypatch.setattr("modules.home.SudokuBacktracking", FailingSolver)
    home._on_solve()

    assert home.status.text == "An unexpected error occurred."
    assert _visual_cell(home, 0, 0).text == "4"


def test_keep_board_square_uses_smaller_dimension(home):
    container = AnchorLayout(size=(400, 200))
    home._keep_board_square(container)
    assert tuple(home.board.size) == (200, 200)


def test_apply_board_fills_digits_and_leaves_zeros_blank(home):
    board = np.zeros((9, 9), dtype=np.uint8)
    board[0, 0] = 7
    board[4, 4] = 3

    home.apply_board(board)

    assert _visual_cell(home, 0, 0).text == "7"
    assert _visual_cell(home, 4, 4).text == "3"
    assert _visual_cell(home, 0, 1).text == ""


def test_apply_board_clears_status(home):
    home.status.text = INVALID_PUZZLE_TEXT
    home.apply_board(np.zeros((9, 9), dtype=np.uint8))
    assert home.status.text == ""


def test_scan_button_triggers_callback():
    called = {"value": False}
    home = Home(on_camera=lambda: called.update(value=True))
    assert home._on_camera is not None
    home._on_camera()
    assert called["value"] is True


def test_select_file_button_triggers_callback():
    called = {"value": False}
    home = Home(on_file_select=lambda: called.update(value=True))
    assert home._on_file_select is not None
    home._on_file_select()
    assert called["value"] is True
