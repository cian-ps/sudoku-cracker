from __future__ import annotations

from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from modules.image_parsing import (
    InferenceEngine,
    ObjectDetectionError,
    OCREngineError,
    OCRMismatchError,
    _OCREngine,
    _reorder,
    draw_contour,
    extract_grid,
)


def _grid_with_populated_cells(
    positions: list[tuple[int, int]], side: int = 450
) -> np.ndarray:
    grid = np.zeros((side, side, 3), dtype=np.uint8)
    cell = side // 9
    for row, col in positions:
        y1, x1 = row * cell, col * cell
        patch = grid[y1 : y1 + cell, x1 : x1 + cell]
        patch[:] = 0
        patch[15:35, 15:35] = 255
    return grid


def _quadrilateral_frame(
    width: int = 640, height: int = 480
) -> tuple[np.ndarray, np.ndarray]:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    points = np.array(
        [[80, 60], [560, 90], [530, 410], [50, 380]],
        dtype=np.int32,
    )
    cv2.fillPoly(frame, [points], (255, 255, 255))
    return frame, points


def test_reorder_maps_corners() -> None:
    points = np.array(
        [
            [[100, 50]],
            [[500, 80]],
            [[480, 400]],
            [[60, 380]],
        ],
        dtype=np.float32,
    )

    ordered = _reorder(points)

    assert ordered.shape == (4, 2)
    assert np.allclose(ordered[0], [100, 50])
    assert np.allclose(ordered[2], [480, 400])


def test_extract_grid_warps_detected_quadrilateral() -> None:
    frame, _ = _quadrilateral_frame()

    warped = extract_grid(frame, side=300)

    assert warped.shape == (300, 300, 3)


def test_extract_grid_raises_when_not_quadrilateral() -> None:
    frame, _ = _quadrilateral_frame()
    bad_approx = np.array([[[0, 0]], [[1, 0]], [[1, 1]]], dtype=np.int32)

    with patch("modules.image_parsing.cv2.approxPolyDP", return_value=bad_approx):
        with pytest.raises(ObjectDetectionError, match="Expected 4 vertices"):
            extract_grid(frame)


def test_draw_contour_draws_on_frame_with_contour() -> None:
    frame, _ = _quadrilateral_frame()
    original = frame.copy()

    draw_contour(frame)

    assert not np.array_equal(frame, original)


def test_inference_engine_parse_to_numpy_success(mock_ocr_engine: MagicMock) -> None:
    mock_ocr_engine.predict.return_value = [{"rec_texts": ["5", "9"]}]
    grid = _grid_with_populated_cells([(0, 0), (0, 1)])

    engine = InferenceEngine()
    result = engine.run(grid)

    assert result.shape == (9, 9)
    assert result[0, 0] == 5
    assert result[0, 1] == 9


def test_inference_engine_filters_non_digit_predictions(
    mock_ocr_engine: MagicMock,
) -> None:
    mock_ocr_engine.predict.return_value = [{"rec_texts": ["5", "x"]}]
    grid = _grid_with_populated_cells([(0, 0), (0, 1)])

    engine = InferenceEngine()
    result = engine.run(grid)

    assert result[0, 0] == 5
    assert result[0, 1] == 0


def test_inference_engine_raises_on_prediction_mismatch(
    mock_ocr_engine: MagicMock,
) -> None:
    mock_ocr_engine.predict.return_value = [{"rec_texts": ["5"]}]
    grid = _grid_with_populated_cells([(0, 0), (0, 1)])

    engine = InferenceEngine()

    with pytest.raises(OCRMismatchError, match="OCR only predicted"):
        engine.run(grid)


def test_inference_engine_parse_empty_grid(mock_ocr_engine: MagicMock) -> None:
    mock_ocr_engine.predict.return_value = [{"rec_texts": []}]
    grid = np.zeros((450, 450, 3), dtype=np.uint8)

    engine = InferenceEngine()
    result = engine.run(grid)

    assert result.shape == (9, 9)
    assert np.all(result == 0)


@pytest.mark.no_mock_ocr
def test_get_paddle_ocr_raises_engine_error() -> None:
    _OCREngine.clear_cache()

    with patch(
        "modules.image_parsing.create_ocr_engine",
        side_effect=OCREngineError("Failed to initialize OCR engine."),
    ):
        with pytest.raises(OCREngineError, match="Failed to initialize OCR engine"):
            _OCREngine._get_paddle_ocr()
