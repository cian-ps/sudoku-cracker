from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from modules.ocr.model_assets import is_android


def load_bgr_image(path: str) -> np.ndarray | None:
    """Load a BGR image from a filesystem path or Android content URI."""
    if path.startswith("content://"):
        if is_android():
            image = _decode_bgr_from_android_uri(path)
            if image is not None:
                return image
        return _load_from_uri(path)

    if is_android():
        image = _decode_bgr_from_android_path(path)
        if image is None:
            image = _load_from_path_bytes(path)
        if image is None:
            logging.error("Failed to decode image from %s", path)
        return image

    image = cv2.imread(path)
    if image is not None:
        return image

    if not os.path.isabs(path):
        logging.error(
            "cv2.imread failed for %r; likely a display name without URI access",
            path,
        )
    else:
        logging.error("cv2.imread failed for %s", path)
    return None


def copy_uri_to_cache(uri: str, *, suffix: str = ".jpg") -> str | None:
    """Copy an Android content URI to app-private storage; return the path."""
    if not is_android():
        logging.error("URI copy is only supported on Android: %s", uri)
        return None

    try:
        from android import mActivity
        from jnius import autoclass
    except ImportError:
        logging.exception("Android modules unavailable for URI copy")
        return None

    Uri = autoclass("android.net.Uri")
    FileOutputStream = autoclass("java.io.FileOutputStream")
    Array = autoclass("java.lang.reflect.Array")
    Byte = autoclass("java.lang.Byte")

    cache_dir = _android_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"picked_image{suffix}"

    parsed = Uri.parse(uri)
    input_stream = mActivity.getContentResolver().openInputStream(parsed)
    if input_stream is None:
        logging.error("openInputStream returned None for %s", uri)
        return None

    buffer = Array.newInstance(Byte.TYPE, 65536)
    output_stream = FileOutputStream(str(dest))
    try:
        while True:
            count = input_stream.read(buffer)
            if count == -1:
                break
            output_stream.write(buffer, 0, count)
    except Exception:
        logging.exception("Failed to copy URI %s", uri)
        return None
    finally:
        input_stream.close()
        output_stream.close()

    size = dest.stat().st_size
    if size == 0:
        logging.error("Copied image is empty for %s", uri)
        return None
    logging.info("Copied image from %s to %s (%d bytes)", uri, dest, size)
    return str(dest)


def _load_from_path_bytes(path: str) -> np.ndarray | None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        logging.exception("Failed to read image bytes from %s", path)
        return None
    if not data:
        logging.error("Image file is empty: %s", path)
        return None

    return _decode_bgr_from_bytes(data, source=path)


def _load_from_uri(uri: str) -> np.ndarray | None:
    data = _read_uri_bytes(uri)
    if data is None:
        logging.error("Failed to read bytes from URI %s", uri)
        return None

    return _decode_bgr_from_bytes(data, source=uri)


def _decode_bgr_from_android_path(path: str) -> np.ndarray | None:
    try:
        from jnius import autoclass
    except ImportError:
        return None

    BitmapFactory = autoclass("android.graphics.BitmapFactory")
    bitmap = BitmapFactory.decodeFile(path)
    if bitmap is None:
        logging.warning("BitmapFactory.decodeFile returned None for %s", path)
        return None

    try:
        return _android_bitmap_to_bgr(bitmap)
    finally:
        bitmap.recycle()


def _decode_bgr_from_android_uri(uri: str) -> np.ndarray | None:
    try:
        from android import mActivity
        from jnius import autoclass
    except ImportError:
        return None

    Uri = autoclass("android.net.Uri")
    BitmapFactory = autoclass("android.graphics.BitmapFactory")

    stream = mActivity.getContentResolver().openInputStream(Uri.parse(uri))
    if stream is None:
        logging.error("openInputStream returned None for %s", uri)
        return None

    try:
        bitmap = BitmapFactory.decodeStream(stream)
    finally:
        stream.close()

    if bitmap is None:
        logging.warning("BitmapFactory.decodeStream returned None for %s", uri)
        return None

    try:
        return _android_bitmap_to_bgr(bitmap)
    finally:
        bitmap.recycle()


def _android_bitmap_to_bgr(bitmap: object) -> np.ndarray:
    from jnius import autoclass

    Integer = autoclass("java.lang.Integer")
    Array = autoclass("java.lang.reflect.Array")

    width = bitmap.getWidth()  # type: ignore[attr-defined]
    height = bitmap.getHeight()  # type: ignore[attr-defined]
    count = width * height
    pixels = Array.newInstance(Integer.TYPE, count)
    bitmap.getPixels(pixels, 0, width, 0, 0, width, height)  # type: ignore[attr-defined]

    arr = np.empty(count, dtype=np.int32)
    for index in range(count):
        arr[index] = pixels[index]

    blue = (arr & 0xFF).astype(np.uint8)
    green = ((arr >> 8) & 0xFF).astype(np.uint8)
    red = ((arr >> 16) & 0xFF).astype(np.uint8)
    bgr = np.stack([blue, green, red], axis=-1).reshape(height, width, 3)
    logging.info(
        "Decoded Android bitmap %dx%d (mean pixel value %.1f)",
        width,
        height,
        float(bgr.mean()),
    )
    return bgr


def _decode_bgr_from_bytes(data: bytes, *, source: str) -> np.ndarray | None:
    try:
        with Image.open(BytesIO(data)) as pil_image:
            rgb = np.asarray(pil_image.convert("RGB"))
    except Exception:
        logging.exception(
            "Failed to decode image bytes from %s (%d bytes, magic=%s)",
            source,
            len(data),
            data[:4].hex() if data else "empty",
        )
        return None

    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _android_cache_dir() -> Path:
    private = os.environ.get("ANDROID_PRIVATE")
    if private:
        return Path(private) / "cache"
    return Path("/tmp/sudoku-cracker-cache")


def _read_uri_bytes(uri: str) -> bytes | None:
    if not is_android():
        logging.error("URI loading is only supported on Android: %s", uri)
        return None

    try:
        from android import mActivity
        from jnius import autoclass
    except ImportError:
        logging.exception("Android modules unavailable for URI loading")
        return None

    Uri = autoclass("android.net.Uri")
    ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
    Array = autoclass("java.lang.reflect.Array")
    Byte = autoclass("java.lang.Byte")

    parsed = Uri.parse(uri)
    stream = mActivity.getContentResolver().openInputStream(parsed)
    if stream is None:
        logging.error("openInputStream returned None for %s", uri)
        return None

    buffer = Array.newInstance(Byte.TYPE, 65536)
    baos = ByteArrayOutputStream()
    try:
        while True:
            count = stream.read(buffer)
            if count == -1:
                break
            baos.write(buffer, 0, count)
        java_bytes = baos.toByteArray()
        return bytes(bytearray(java_bytes))
    except Exception:
        logging.exception("Failed to read URI %s", uri)
        return None
    finally:
        stream.close()
