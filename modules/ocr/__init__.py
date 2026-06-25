from modules.ocr.errors import OCREngineError
from modules.ocr.factory import create_ocr_engine
from modules.ocr.paddle_backend import PaddleBackend
from modules.ocr.protocol import OCRBackend
from modules.ocr.rapidocr_backend import RapidOCRBackend

__all__ = [
    "OCRBackend",
    "OCREngineError",
    "PaddleBackend",
    "RapidOCRBackend",
    "create_ocr_engine",
]
