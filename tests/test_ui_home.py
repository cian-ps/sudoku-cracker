import numpy as np
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput

from main import Home
from main import ERROR_TEXT

EMPTY_BOARD_SOLUTION = np.array(
    [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [2, 1, 4, 3, 6, 5, 8, 9, 7],
        [3, 6, 5, 8, 9, 7, 2, 1, 4],
        [8, 9, 7, 2, 1, 4, 3, 6, 5],
        [5, 3, 1, 6, 4, 2, 9, 7, 8],
        [6, 4, 2, 9, 7, 8, 5, 3, 1],
        [9, 7, 8, 5, 3, 1, 6, 4, 2],
    ],
    dtype=np.int64,
)

EXAMPLE = np.array(
    [
        [4, 0, 0, 6, 0, 0, 0, 0, 2],
        [1, 0, 2, 0, 8, 5, 0, 0, 0],
        [0, 0, 5, 9, 1, 0, 0, 3, 8],
        [0, 7, 8, 0, 0, 9, 2, 0, 0],
        [0, 4, 0, 0, 3, 0, 0, 9, 0],
        [0, 0, 3, 5, 0, 0, 1, 7, 0],
        [8, 5, 0, 0, 9, 6, 7, 0, 0],
        [0, 0, 0, 8, 2, 0, 6, 0, 9],
        [2, 0, 0, 0, 0, 1, 0, 0, 4],
    ],
    dtype=np.int64,
)

EXAMPLE_SOLUTION = np.array(
    [
        [4, 8, 9, 6, 7, 3, 5, 1, 2],
        [1, 3, 2, 4, 8, 5, 9, 6, 7],
        [7, 6, 5, 9, 1, 2, 4, 3, 8],
        [5, 7, 8, 1, 6, 9, 2, 4, 3],
        [6, 4, 1, 2, 3, 7, 8, 9, 5],
        [9, 2, 3, 5, 4, 8, 1, 7, 6],
        [8, 5, 4, 3, 9, 6, 7, 2, 1],
        [3, 1, 7, 8, 2, 4, 6, 5, 9],
        [2, 9, 6, 7, 5, 1, 3, 8, 4],
    ],
    dtype=np.int64,
)


def _set_cell(home, row, col, value):
    home.cells[Home._cell_index(row, col)].text = str(value)


def _visual_cell(home, row, col):
    """Return the TextInput widget at the on-screen (row, col) position."""
    block_row, block_col = row // 3, col // 3
    inner_row, inner_col = row % 3, col % 3
    blocks = list(reversed(home.board.children))
    block = blocks[block_row * 3 + block_col]
    cells_in_block = list(reversed(block.children))
    return cells_in_block[inner_row * 3 + inner_col]


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


def test_board_to_ndarray_empty(home):
    board = home._board_to_ndarray()
    assert board.shape == (9, 9)
    assert board.dtype == np.int64
    assert np.all(board == 0)


def test_board_to_ndarray_reads_row_major(home):
    _set_cell(home, 0, 0, 5)
    _set_cell(home, 1, 2, 9)
    _set_cell(home, 8, 8, 1)

    board = home._board_to_ndarray()
    assert board[0, 0] == 5
    assert board[1, 2] == 9
    assert board[8, 8] == 1


def test_apply_solution_writes_cells(home):
    home._apply_solution(EMPTY_BOARD_SOLUTION)

    for row in range(9):
        for col in range(9):
            assert _visual_cell(home, row, col).text == str(
                EMPTY_BOARD_SOLUTION[row, col]
            )


def test_on_clear_empties_all_cells(home):
    _set_cell(home, 0, 0, 1)
    _set_cell(home, 4, 4, 5)
    _set_cell(home, 8, 8, 9)

    home._on_clear()

    assert all(cell.text == "" for cell in home.cells)


def test_on_clear_resets_status(home):
    home.status.text = ERROR_TEXT
    home._on_clear()
    assert home.status.text == ""


def test_on_solve_resets_status(home):
    home.status.text = ERROR_TEXT
    home._on_solve()
    assert home.status.text == ""


def test_on_solve_empty_board(home):
    home._on_solve()

    for row in range(9):
        for col in range(9):
            assert _visual_cell(home, row, col).text == str(
                EMPTY_BOARD_SOLUTION[row, col]
            )


def test_on_solve_example(home):
    for row in range(9):
        for col in range(9):
            val = EXAMPLE[row, col]
            if val:
                _set_cell(home, row, col, val)

    home._on_solve()

    for row in range(9):
        for col in range(9):
            assert _visual_cell(home, row, col).text == str(EXAMPLE_SOLUTION[row, col])


def test_on_solve_example_via_visual_cells(home):
    for row in range(9):
        for col in range(9):
            val = EXAMPLE[row, col]
            if val:
                _visual_cell(home, row, col).text = str(val)

    home._on_solve()

    for row in range(9):
        for col in range(9):
            assert _visual_cell(home, row, col).text == str(EXAMPLE_SOLUTION[row, col])


def test_on_solve_invalid_puzzle_sets_status(home):
    _set_cell(home, 0, 0, 1)
    _set_cell(home, 0, 1, 1)

    home._on_solve()

    assert home.status.text == ERROR_TEXT
    assert _visual_cell(home, 0, 0).text == "1"
    assert _visual_cell(home, 0, 1).text == "1"


def test_keep_board_square_uses_smaller_dimension(home):
    container = AnchorLayout(size=(400, 200))
    home._keep_board_square(container)
    assert tuple(home.board.size) == (200, 200)
