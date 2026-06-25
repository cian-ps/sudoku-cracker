from __future__ import annotations

import os
from typing import Literal

from modules.ocr.errors import OCREngineError
from modules.ocr.paddle_backend import PaddleBackend
from modules.ocr.protocol import OCRBackend
from modules.ocr.rapidocr_backend import RapidOCRBackend

OCRBackendName = Literal["paddle", "rapidocr"]
_DEFAULT_BACKEND: OCRBackendName = "rapidocr"


def _default_backend_name() -> OCRBackendName:
    try:
        from kivy.utils import platform as kivy_platform

        if kivy_platform == "android":
            return "rapidocr"
    except (ImportError, ModuleNotFoundError):
        pass
    return _DEFAULT_BACKEND


def _normalize_backend_name(value: str | None) -> OCRBackendName:
    if value is None:
        return _default_backend_name()

    normalized = value.strip().lower()
    if normalized in {"paddle", "rapidocr"}:
        return normalized  # type: ignore[return-value]

    raise OCREngineError(f"Unsupported OCR backend: {value}")


def create_ocr_engine(
    backend: OCRBackendName | None = None,
) -> OCRBackend:
    selected = backend or _normalize_backend_name(os.environ.get("OCR_BACKEND"))

    if selected == "paddle":
        return PaddleBackend()
    if selected == "rapidocr":
        return RapidOCRBackend()

    raise OCREngineError(f"Unsupported OCR backend: {selected}")
