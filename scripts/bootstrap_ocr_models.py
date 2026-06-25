#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rapidocr  # noqa: E402

from modules.ocr.model_assets import ocr_manifest_path, ocr_model_dir  # noqa: E402
from modules.ocr.rapidocr_backend import RapidOCRBackend  # noqa: E402

EXPECTED_MODELS = {
    "det": "ch_PP-OCRv5_det_server.onnx",
    "rec": "en_PP-OCRv5_rec_mobile.onnx",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    model_dir = ocr_model_dir()
    manifest_path = ocr_manifest_path()
    model_dir.mkdir(parents=True, exist_ok=True)

    RapidOCRBackend()

    source_dir = Path(rapidocr.__file__).resolve().parent / "models"
    manifest: dict[str, dict[str, str]] = {"det": {}, "rec": {}}

    for role, filename in EXPECTED_MODELS.items():
        source_path = source_dir / filename
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Expected RapidOCR model not found after warmup: {source_path}"
            )

        target_path = model_dir / filename
        shutil.copy2(source_path, target_path)
        manifest[role] = {
            "filename": filename,
            "sha256": _sha256(target_path),
        }

    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
        manifest_file.write("\n")

    print(f"Cached OCR models in {model_dir}")
    print(f"Wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
