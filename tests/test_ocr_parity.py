from __future__ import annotations

from pathlib import Path

import importlib.util

import cv2
import numpy as np
import pytest

from modules.image_parsing import InferenceEngine, _OCREngine, extract_grid
from modules.ocr.factory import create_ocr_engine
from modules.ocr.paddle_backend import PaddleBackend
from modules.ocr.rapidocr_backend import RapidOCRBackend

# Single-puzzle photo with stable Paddle/RapidOCR parity. The printable page image
# can differ by one digit due to ONNX vs Paddle inference on the same weights.
PARITY_IMAGE_PATHS = [
    Path("data/sudoku_puzzles_book_33.jpg"),
]


def _paddle_available() -> bool:
    return importlib.util.find_spec("paddleocr") is not None


def _require_paddle() -> None:
    if not _paddle_available():
        pytest.skip("paddleocr optional extra is not installed")


def _extract_rec_texts(
    backend: PaddleBackend | RapidOCRBackend, grid: np.ndarray
) -> list[str]:
    return backend.predict(grid)[0]["rec_texts"]


def _run_board(
    backend: PaddleBackend | RapidOCRBackend, grid: np.ndarray
) -> np.ndarray:
    _OCREngine.clear_cache()
    engine = InferenceEngine()
    engine._ocr = backend
    return engine.run(grid)


@pytest.mark.integration
@pytest.mark.no_mock_ocr
@pytest.mark.parametrize("image_path", PARITY_IMAGE_PATHS, ids=lambda path: path.name)
def test_rapidocr_rec_texts_match_paddle(image_path: Path) -> None:
    _require_paddle()
    frame = cv2.imread(str(image_path))
    assert frame is not None

    grid = extract_grid(frame)
    paddle_backend = PaddleBackend()
    rapid_backend = RapidOCRBackend()

    paddle_texts = _extract_rec_texts(paddle_backend, grid)
    rapid_texts = _extract_rec_texts(rapid_backend, grid)

    assert paddle_texts == rapid_texts


@pytest.mark.integration
@pytest.mark.no_mock_ocr
@pytest.mark.parametrize("image_path", PARITY_IMAGE_PATHS, ids=lambda path: path.name)
def test_rapidocr_board_matches_paddle(image_path: Path) -> None:
    _require_paddle()
    frame = cv2.imread(str(image_path))
    assert frame is not None

    grid = extract_grid(frame)
    paddle_backend = PaddleBackend()
    rapid_backend = RapidOCRBackend()

    paddle_board = _run_board(paddle_backend, grid)
    rapid_board = _run_board(rapid_backend, grid)

    assert np.array_equal(paddle_board, rapid_board)


@pytest.mark.integration
@pytest.mark.no_mock_ocr
def test_factory_can_build_rapidocr_backend() -> None:
    rapid = create_ocr_engine(backend="rapidocr")
    assert isinstance(rapid, RapidOCRBackend)


@pytest.mark.integration
@pytest.mark.no_mock_ocr
def test_factory_can_build_paddle_backend() -> None:
    _require_paddle()

    paddle = create_ocr_engine(backend="paddle")
    assert isinstance(paddle, PaddleBackend)
