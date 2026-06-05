import pytest

from modules.backtracking import SudokuBacktracking
import numpy as np


def test_is_valid_number_in_cell():
    mat = np.zeros((9, 9), dtype=np.int64)
    mat[0, 0] = 1

    solver = SudokuBacktracking(mat)
    assert solver._SudokuBacktracking__is_valid(1, (1, 3))
    assert not solver._SudokuBacktracking__is_valid(1, (1, 2))
    assert not solver._SudokuBacktracking__is_valid(1, (0, 3))
    assert not solver._SudokuBacktracking__is_valid(1, (3, 0))


def test_recursion_limit():
    solver = SudokuBacktracking(np.zeros((9, 9), dtype=np.int64))
    solver._SudokuBacktracking__n_recursions = 1000
    with pytest.raises(RecursionError):
        solver.get_solution()


def test_raises_recursion_error():
    mat = np.zeros((9, 9), dtype=np.int64)
    mat[0, 0] = 1
    mat[0, 1] = 1
    solver = SudokuBacktracking(mat)
    with pytest.raises(RecursionError):
        solver.get_solution()


def test_get_solution():
    solution = np.array(
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
    solver = SudokuBacktracking(np.zeros((9, 9), dtype=np.int64))
    assert np.array_equal(solver.get_solution(), solution)
