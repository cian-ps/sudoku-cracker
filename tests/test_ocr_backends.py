from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from modules.image_parsing import OCREngineError
from modules.ocr.factory import create_ocr_engine
from modules.ocr.paddle_backend import PaddleBackend
from modules.ocr.rapidocr_backend import RapidOCRBackend


def test_create_ocr_engine_defaults_to_paddle() -> None:
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OCR_BACKEND", None)
        with patch("modules.ocr.factory.PaddleBackend") as mock_paddle:
            mock_paddle.return_value = MagicMock()
            engine = create_ocr_engine()
            mock_paddle.assert_called_once()
            assert engine is mock_paddle.return_value


def test_create_ocr_engine_honors_rapidocr_env() -> None:
    with patch.dict(os.environ, {"OCR_BACKEND": "rapidocr"}, clear=False):
        with patch("modules.ocr.factory.RapidOCRBackend") as mock_rapid:
            mock_rapid.return_value = MagicMock()
            engine = create_ocr_engine()
            mock_rapid.assert_called_once()
            assert engine is mock_rapid.return_value


def test_create_ocr_engine_rejects_unknown_backend() -> None:
    with pytest.raises(OCREngineError, match="Unsupported OCR backend"):
        create_ocr_engine(backend="unknown")  # type: ignore[arg-type]


def test_rapidocr_backend_predict_returns_contract_shape() -> None:
    backend = RapidOCRBackend()
    mock_result = MagicMock()
    mock_result.txts = ["5", "9"]
    backend._ocr = MagicMock(return_value=mock_result)

    prediction = backend.predict(np.zeros((450, 450, 3), dtype=np.uint8))

    assert prediction == [{"rec_texts": ["5", "9"]}]


def test_rapidocr_backend_predict_empty_result() -> None:
    backend = RapidOCRBackend()
    backend._ocr = MagicMock(return_value=None)

    prediction = backend.predict(np.zeros((450, 450, 3), dtype=np.uint8))

    assert prediction == [{"rec_texts": []}]


def test_paddle_backend_normalizes_json_payload() -> None:
    backend = PaddleBackend.__new__(PaddleBackend)
    mock_result = MagicMock()
    mock_result.json = {"res": {"rec_texts": ["1", "2"]}}
    backend._ocr = MagicMock(predict=MagicMock(return_value=[mock_result]))

    prediction = backend.predict(np.zeros((450, 450, 3), dtype=np.uint8))

    assert prediction == [{"rec_texts": ["1", "2"]}]
