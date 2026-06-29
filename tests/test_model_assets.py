from __future__ import annotations

from pathlib import Path

from modules.ocr.model_assets import (
    app_root,
    is_android,
    ocr_manifest_path,
    ocr_model_dir,
    resolve_local_model_paths,
)


def test_app_root_uses_android_private(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANDROID_APP_PATH", str(tmp_path))
    (tmp_path / "assets" / "models" / "ocr").mkdir(parents=True)
    (tmp_path / "assets" / "models" / "ocr_models.json").write_text(
        '{"det":{"filename":"det.onnx"},"rec":{"filename":"rec.onnx"}}',
        encoding="utf-8",
    )
    (tmp_path / "assets" / "models" / "ocr" / "det.onnx").write_bytes(b"det")
    (tmp_path / "assets" / "models" / "ocr" / "rec.onnx").write_bytes(b"rec")

    assert is_android()
    assert app_root() == tmp_path
    assert ocr_model_dir() == tmp_path / "assets" / "models" / "ocr"
    assert ocr_manifest_path() == tmp_path / "assets" / "models" / "ocr_models.json"

    paths = resolve_local_model_paths()
    assert paths is not None
    assert paths["Det.model_path"].endswith("det.onnx")
    assert paths["Rec.model_path"].endswith("rec.onnx")


def test_app_root_falls_back_to_android_private_app_dir(
    monkeypatch, tmp_path: Path
) -> None:
    app_dir = tmp_path / "app"
    monkeypatch.setenv("ANDROID_PRIVATE", str(tmp_path))
    (app_dir / "assets" / "models" / "ocr").mkdir(parents=True)
    (app_dir / "assets" / "models" / "ocr_models.json").write_text(
        '{"det":{"filename":"det.onnx"},"rec":{"filename":"rec.onnx"}}',
        encoding="utf-8",
    )
    (app_dir / "assets" / "models" / "ocr" / "det.onnx").write_bytes(b"det")
    (app_dir / "assets" / "models" / "ocr" / "rec.onnx").write_bytes(b"rec")

    assert app_root() == app_dir
    assert resolve_local_model_paths() is not None
