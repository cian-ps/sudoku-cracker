from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from modules.ocr.factory import create_ocr_engine
from modules.ocr.rapidocr_backend import RapidOCRBackend


def test_create_ocr_engine_returns_rapidocr_backend() -> None:
    with patch("modules.ocr.factory.RapidOCRBackend") as mock_rapid:
        mock_rapid.return_value = MagicMock()
        engine = create_ocr_engine()
        mock_rapid.assert_called_once()
        assert engine is mock_rapid.return_value


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
