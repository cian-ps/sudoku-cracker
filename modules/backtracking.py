from __future__ import annotations

import numpy as np
from typing import Tuple
import sys


_RECURSION_LIMIT = 100000
sys.setrecursionlimit(_RECURSION_LIMIT)


class SudokuBacktracking:
    """
    Algorithm that solves any valid 9x9 sudoku puzzle, using recursive backtracking.

    Args:
        mat (numpy.ndarray): 9x9 matrix representing the sudoku puzzle.
    """

    def __init__(self, mat: np.ndarray) -> None:
        self.__n_recursions = 0
        self.__mat = mat

    def __is_valid(self, num: int, cell: Tuple[int, int]) -> bool:
        # check 3x3 subgrid
        row, col = cell
        for i in range(row // 3 * 3, row // 3 * 3 + 3):
            for j in range(col // 3 * 3, col // 3 * 3 + 3):
                if self.__mat[i, j] == num:
                    return False

        # check row and column
        for i in range(9):
            if self.__mat[row, i] == num or self.__mat[i, col] == num:
                return False

        return True

    def __solve(self, row: int, col: int) -> bool:
        self.__n_recursions += 1
        if self.__n_recursions >= _RECURSION_LIMIT - 1:
            raise RecursionError(
                f"attempted {self.__n_recursions + 1} of {_RECURSION_LIMIT} maximum allowed recursions"
            )

        # base case
        if row == 8 and col == 9:
            return True

        # move to the next row
        if col == 9:
            row += 1
            col = 0

        # move forward if cell is filled
        if self.__mat[row, col] != 0:
            return self.__solve(row, col + 1)

        # backtracking
        for i in range(1, 10):
            if self.__is_valid(i, (row, col)):
                self.__mat[row, col] = i
                if self.__solve(row, col + 1):
                    return True
                self.__mat[row, col] = 0

        return False

    def get_solution(self) -> np.ndarray:
        """
        Returns the solution to the sudoku puzzle.

        Returns:
            numpy.ndarray: The solution to the sudoku puzzle.
        """
        self.__solve(0, 0)
        return self.__mat
