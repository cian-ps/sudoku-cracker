from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OCR_MODEL_DIR = PROJECT_ROOT / "assets" / "models" / "ocr"
MANIFEST_PATH = PROJECT_ROOT / "assets" / "models" / "ocr_models.json"


def resolve_local_model_paths() -> dict[str, str] | None:
    if not MANIFEST_PATH.is_file():
        return None

    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        manifest: dict[str, Any] = json.load(manifest_file)

    det_name = manifest.get("det", {}).get("filename")
    rec_name = manifest.get("rec", {}).get("filename")
    if not det_name or not rec_name:
        return None

    det_path = OCR_MODEL_DIR / det_name
    rec_path = OCR_MODEL_DIR / rec_name
    if not det_path.is_file() or not rec_path.is_file():
        return None

    return {
        "Det.model_path": str(det_path.resolve()),
        "Rec.model_path": str(rec_path.resolve()),
    }
