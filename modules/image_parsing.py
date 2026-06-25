from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import cv2
import numpy as np

from modules.ocr.errors import OCREngineError
from modules.ocr.factory import create_ocr_engine


class OCRMismatchError(Exception):
    """
    Exception raised when the number of predictions does not match the number of populated cells.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ObjectDetectionError(Exception):
    """
    Exception raised when object detection fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class _OCREngine:
    _instance: Any | None = None
    _lock = threading.Lock()
    _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="paddle_ocr")

    @classmethod
    def _get_paddle_ocr(cls) -> Any:
        if _OCREngine._instance is not None:
            return _OCREngine._instance

        with cls._lock:
            if _OCREngine._instance is not None:
                return _OCREngine._instance

            try:
                _OCREngine._instance = create_ocr_engine()
            except OCREngineError:
                raise
            except Exception as exc:
                raise OCREngineError("Failed to initialize OCR engine.") from exc

        return _OCREngine._instance

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            _OCREngine._instance = None

    def __init__(self) -> None:
        self._ocr = self._get_paddle_ocr()

    def _predict(self, image: np.ndarray) -> list[Any]:
        return self._ocr.predict(image)


class InferenceEngine(_OCREngine):
    """
    Sudoku puzzle image to array parser.
    """

    def __init__(self) -> None:
        super().__init__()

    def __split_grid(self, grid: np.ndarray) -> list[np.ndarray]:
        cells = []

        cell_h = grid.shape[0] // 9
        cell_w = grid.shape[1] // 9

        for i in range(9):
            for j in range(9):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                cell = grid[y1:y2, x1:x2]
                cells.append(cell)

        return cells

    def __predict_digits(self, grid: np.ndarray) -> list[int]:
        allowed_chars = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
        results = self._predict(grid)
        preds = results[0]["rec_texts"]
        return list(map(lambda x: int(x) if x in allowed_chars else 0, preds))

    def __std_masking(
        self, grid: np.ndarray, std_thresh: int, padding: int
    ) -> np.ndarray:
        cells_list = []
        for c in self.__split_grid(grid):
            gray = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
            cells_list.append(gray[padding:-padding, padding:-padding])

        cells = np.array(cells_list)
        std_mask = np.std(cells, axis=(1, 2)) > std_thresh
        std_mask = std_mask.reshape(9, 9)

        return std_mask

    def __parse_to_numpy(
        self, grid: np.ndarray, std_thresh: int, padding: int
    ) -> np.ndarray:
        result = np.zeros((9, 9), dtype=np.uint8)
        preds = self.__predict_digits(grid)
        std_mask = self.__std_masking(grid, std_thresh, padding)
        expected_len = int(np.sum(std_mask))
        if len(preds) != expected_len:
            raise OCRMismatchError(
                f"OCR only predicted {len(preds)} of {expected_len} expected digits."
            )

        result[std_mask] = preds
        return result

    def run(
        self, grid: np.ndarray, std_thresh: int = 10, padding: int = 10
    ) -> np.ndarray:
        """
        Run OCR inference on a dedicated worker thread.

        Args:
            grid(np.ndarray): Clear image only showing a square Sudoku grid.
            std_thresh(int): Threshold for detecting populated cells by standard deviation.
                Defaults to 10.
            padding(int): Cell padding to exclude grid lines when calculating standard deviation.
                Defaults to 10.

        Returns:
            An ndarray, of shape (9, 9), of recognized digits mapped to their place in the sudoku puzzle.

        Raises:
            OCRMismatchError: If the number of predictions does not match the number of populated cells.
            OCREngineError: If the OCR engine cannot be initialized.
        """

        def execute() -> np.ndarray:
            return self.__parse_to_numpy(grid, std_thresh, padding)

        return self._executor.submit(execute).result()


def _threshold(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    return cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )


def draw_contour(frame: np.ndarray) -> None:
    """
    Draws the largest contour onto the given frame inplace.

    Args:
        frame(np.ndarray): The frame to draw the contour onto.
    """
    thresh = _threshold(frame)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_contour = max(contours, key=cv2.contourArea)
    cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 5)


def _reorder(points: np.ndarray) -> np.ndarray:
    points = points.reshape((4, 2))
    new_points = np.zeros((4, 2), dtype=np.float32)

    add = points.sum(1)
    new_points[0] = points[np.argmin(add)]  # top-left
    new_points[2] = points[np.argmax(add)]  # bottom-right

    diff = np.diff(points, axis=1)
    new_points[1] = points[np.argmin(diff)]  # top-right
    new_points[3] = points[np.argmax(diff)]  # bottom-left

    return new_points


def extract_grid(img: np.ndarray, side: int = 450) -> np.ndarray:
    """
    Extracts a quadrilateral object from the given image.

    Args:
        img(np.ndarray): Image or video frame.
        side(int): Side length of the output.
    Returns:
        np.ndarray: The extracted object as a square.
    Raises:
        ObjectDetectionError: If no quadrilateral object can be detected.
    """
    img_thresh = _threshold(img)
    contours, _ = cv2.findContours(
        img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contour = max(contours, key=cv2.contourArea)

    peri = cv2.arcLength(contour, True)

    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

    if not len(approx) == 4:
        raise ObjectDetectionError(
            f"Invalid shape {approx.shape}: Expected 4 vertices got {len(approx)}."
        )

    points = _reorder(approx)

    pts1 = np.asarray(points, dtype=np.float32)
    pts2 = np.asarray(
        [[0, 0], [side, 0], [side, side], [0, side]],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img, matrix, (side, side))

    return warped
