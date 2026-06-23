from __future__ import annotations

import threading
from typing import Any

import cv2
import numpy as np

_ocr_instance: Any | None = None
_ocr_lock = threading.Lock()


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


class OCREngineError(Exception):
    """
    Exception raised when the OCR engine cannot be initialized.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


def _get_paddle_ocr() -> Any:
    global _ocr_instance

    if _ocr_instance is not None:
        return _ocr_instance

    with _ocr_lock:
        if _ocr_instance is not None:
            return _ocr_instance

        try:
            from paddleocr import PaddleOCR

            _ocr_instance = PaddleOCR(lang="en")
        except Exception as exc:
            raise OCREngineError("Failed to initialize OCR engine.") from exc

    return _ocr_instance


def clear_ocr_engine_cache() -> None:
    global _ocr_instance

    with _ocr_lock:
        _ocr_instance = None


class _OCREngine:
    def __init__(self) -> None:
        self._ocr = _get_paddle_ocr()

    def predict(self, image: np.ndarray) -> list[Any]:
        """
        Returns PaddleOCR's predictions for the given image.

        Args:
            image(np.ndarray): The image to pass to PaddleOCR.
        Returns:
            list[Any]: The predictions as returned by PaddleOCR(lang='en').predict(image).
        """
        return self._ocr.predict(image)


class InferenceEngine(_OCREngine):
    """
    Image to ndarray Parser.

    Args:
        grid(np.ndarray): Clear image only showing the Sudoku grid.
        std_thresh(int): Threshold for detecting populated cells by standard deviation.
        padding(int): Cell padding to exclude grid lines when calculating standard deviation.
    """

    def __init__(
        self, grid: np.ndarray, std_thresh: int = 10, padding: int = 10
    ) -> None:
        super().__init__()
        self._grid = grid
        self._cells = self.__split_grid()
        self._preds = self.__predict_digits()
        self._std_mask = self.__std_masking(std_thresh, padding)

    def __split_grid(self) -> list[np.ndarray]:
        cells = []

        cell_h = self._grid.shape[0] // 9
        cell_w = self._grid.shape[1] // 9

        for i in range(9):
            for j in range(9):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                cell = self._grid[y1:y2, x1:x2]
                cells.append(cell)

        return cells

    def __predict_digits(self) -> list[int]:
        allowed_chars = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
        results = self.predict(self._grid)
        preds = results[0]["rec_texts"]
        return list(map(lambda x: int(x) if x in allowed_chars else 0, preds))

    def __std_masking(self, std_thresh: int, padding: int) -> np.ndarray:
        cells_list = []
        for c in self._cells:
            gray = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
            cells_list.append(gray[padding:-padding, padding:-padding])

        cells = np.array(cells_list)
        std_mask = np.std(cells, axis=(1, 2)) > std_thresh
        std_mask = std_mask.reshape(9, 9)

        return std_mask

    def parse_to_numpy(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: 9x9 numpy array from the OCR results.
        Raises:
            OCRMismatchError: If the number of predictions does not match the number of populated cells.
        """
        result = np.zeros((9, 9), dtype=np.int64)
        expected_len = int(np.sum(self._std_mask))
        if len(self._preds) != expected_len:
            raise OCRMismatchError(
                f"OCR only predicted {len(self._preds)} of {expected_len} expected digits."
            )

        result[self._std_mask] = self._preds
        return result


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
