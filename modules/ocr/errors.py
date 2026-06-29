from __future__ import annotations


class OCREngineError(Exception):
    """Exception raised when the OCR engine cannot be initialized."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
