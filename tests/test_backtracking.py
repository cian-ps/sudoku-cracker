import numpy as np
import pytest

from modules.backtracking import SudokuBacktracking
from modules.backtracking import _RECURSION_LIMIT


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
    solver._SudokuBacktracking__n_recursions = _RECURSION_LIMIT
    with pytest.raises(RecursionError):
        solver.get_solution()


def test_raises_recursion_error():
    mat = np.zeros((9, 9), dtype=np.int64)
    mat[0, 0] = 1
    mat[0, 1] = 1
    solver = SudokuBacktracking(mat)
    with pytest.raises(RecursionError):
        solver.get_solution()


def test_get_solution(example, example_solution):
    solver = SudokuBacktracking(example.copy())
    assert np.array_equal(solver.get_solution(), example_solution)
