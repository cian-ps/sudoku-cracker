import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from kivy.config import Config

from modules.home import Home
from modules.image_parsing import clear_ocr_engine_cache

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

Config.set("graphics", "headless", "1")
Config.set("kivy", "log_level", "error")
Config.write()


@pytest.fixture(autouse=True)
def mock_ocr_engine(request: pytest.FixtureRequest) -> Iterator[MagicMock | None]:
    clear_ocr_engine_cache()
    if request.node.get_closest_marker("no_mock_ocr") is not None:
        yield None
        clear_ocr_engine_cache()
        return

    mock_ocr = MagicMock()
    mock_ocr.predict.return_value = [{"rec_texts": []}]
    with patch("modules.image_parsing._get_paddle_ocr", return_value=mock_ocr):
        yield mock_ocr
    clear_ocr_engine_cache()


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


@pytest.fixture
def unsolvable_puzzle():
    return np.array(
        [
            [1, 2, 3, 4, 0, 0, 0, 0, 0],
            [2, 3, 1, 0, 5, 0, 0, 0, 0],
            [3, 1, 2, 0, 0, 6, 0, 0, 0],
            [5, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 6, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 4, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        dtype=np.int64,
    )
