from __future__ import annotations

from modules.ocr.protocol import OCRBackend
from modules.ocr.rapidocr_backend import RapidOCRBackend


def create_ocr_engine() -> OCRBackend:
    return RapidOCRBackend()
