import os

import numpy as np
import pytest
from kivy.config import Config

from main import Home

os.environ.setdefault("KIVY_NO_ARGS", "1")

Config.set("graphics", "headless", "1")
Config.set("kivy", "log_level", "error")
Config.write()


@pytest.fixture
def home():
    return Home()


@pytest.fixture
def example():
    return np.array(
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


@pytest.fixture
def example_solution():
    return np.array(
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
