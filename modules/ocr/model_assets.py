from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def is_android() -> bool:
    return bool(os.environ.get("ANDROID_PRIVATE"))


def app_root() -> Path:
    private = os.environ.get("ANDROID_PRIVATE")
    if private:
        return Path(private)
    return Path(__file__).resolve().parents[2]


def ocr_model_dir() -> Path:
    return app_root() / "assets" / "models" / "ocr"


def ocr_manifest_path() -> Path:
    return app_root() / "assets" / "models" / "ocr_models.json"


def ocr_config_path() -> Path:
    return app_root() / "assets" / "models" / "ocr_config.yaml"


def resolve_local_model_paths() -> dict[str, str] | None:
    manifest_path = ocr_manifest_path()
    if not manifest_path.is_file():
        return None

    with manifest_path.open(encoding="utf-8") as manifest_file:
        manifest: dict[str, Any] = json.load(manifest_file)

    det_name = manifest.get("det", {}).get("filename")
    rec_name = manifest.get("rec", {}).get("filename")
    if not det_name or not rec_name:
        return None

    model_dir = ocr_model_dir()
    det_path = model_dir / det_name
    rec_path = model_dir / rec_name
    if not det_path.is_file() or not rec_path.is_file():
        return None

    return {
        "Det.model_path": str(det_path.resolve()),
        "Rec.model_path": str(rec_path.resolve()),
    }
