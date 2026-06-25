from __future__ import annotations

from typing import Any

import numpy as np

from modules.ocr.errors import OCREngineError


class PaddleBackend:
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(lang="en")
        except Exception as exc:
            raise OCREngineError("Failed to initialize OCR engine.") from exc

    def predict(self, image: np.ndarray) -> list[dict[str, Any]]:
        results = self._ocr.predict(image)
        normalized: list[dict[str, Any]] = []
        for result in results:
            if hasattr(result, "json"):
                payload = result.json
            elif isinstance(result, dict):
                payload = result
            else:
                payload = {}

            if isinstance(payload, dict) and "res" in payload:
                payload = payload["res"]

            if isinstance(payload, dict):
                normalized.append({"rec_texts": list(payload.get("rec_texts", []))})
            else:
                normalized.append({"rec_texts": []})

        if not normalized:
            return [{"rec_texts": []}]
        return normalized
