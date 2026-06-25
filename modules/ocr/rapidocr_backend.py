from __future__ import annotations

from typing import Any

import numpy as np
import yaml
from rapidocr import RapidOCR
from rapidocr.utils.typings import LangDet, LangRec, ModelType, OCRVersion

from modules.ocr.errors import OCREngineError
from modules.ocr.model_assets import (
    is_android,
    ocr_config_path,
    resolve_local_model_paths,
)


def _load_config() -> dict[str, Any]:
    config_path = ocr_config_path()
    if not config_path.is_file():
        return {}
    with config_path.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


def _build_rapidocr_params(config: dict[str, Any]) -> dict[str, Any]:
    det = config.get("det", {})
    rec = config.get("rec", {})
    global_cfg = config.get("global", {})

    params: dict[str, Any] = {
        "Global.use_cls": global_cfg.get("use_cls", False),
        "Global.log_level": global_cfg.get("log_level", "error"),
        "Det.lang_type": LangDet[det.get("lang_type", "CH").upper()],
        "Det.model_type": ModelType[det.get("model_type", "SERVER").upper()],
        "Det.ocr_version": OCRVersion[det.get("ocr_version", "PPOCRV5").upper()],
        "Rec.lang_type": LangRec[rec.get("lang_type", "EN").upper()],
        "Rec.model_type": ModelType[rec.get("model_type", "MOBILE").upper()],
        "Rec.ocr_version": OCRVersion[rec.get("ocr_version", "PPOCRV5").upper()],
        "Det.box_thresh": det.get("box_thresh", 0.5),
        "Det.unclip_ratio": det.get("unclip_ratio", 1.6),
        "Det.thresh": det.get("thresh", 0.3),
    }
    params.update(resolve_local_model_paths() or {})
    return params


def _require_bundled_models_on_android() -> None:
    if not is_android():
        return
    if resolve_local_model_paths() is not None:
        return
    raise OCREngineError(
        "Bundled OCR models not found on Android. "
        "Run `uv run python scripts/bootstrap_ocr_models.py` before building the APK."
    )


class RapidOCRBackend:
    def __init__(self) -> None:
        _require_bundled_models_on_android()
        config = _load_config()
        config_path = config.get("config_path")
        params = _build_rapidocr_params(config)
        try:
            if config_path:
                self._ocr = RapidOCR(config_path=config_path, params=params)
            else:
                self._ocr = RapidOCR(params=params)
        except Exception as exc:
            raise OCREngineError("Failed to initialize OCR engine.") from exc

        runtime = config.get("runtime", {})
        self._use_det = runtime.get("use_det", True)
        self._use_cls = runtime.get("use_cls", False)
        self._use_rec = runtime.get("use_rec", True)

    def predict(self, image: np.ndarray) -> list[dict[str, Any]]:
        result = self._ocr(
            image,
            use_det=self._use_det,
            use_cls=self._use_cls,
            use_rec=self._use_rec,
        )
        if result is None or not result.txts:
            return [{"rec_texts": []}]

        return [{"rec_texts": [str(text) for text in result.txts]}]
