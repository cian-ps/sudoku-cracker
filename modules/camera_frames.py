from __future__ import annotations

import logging

import cv2
import numpy as np
from kivy.graphics.texture import Texture


def nv21_bytes_to_bgr(buffer: bytes, width: int, height: int) -> np.ndarray:
    arr = np.frombuffer(buffer, dtype=np.uint8).reshape((height + height // 2, width))
    return cv2.cvtColor(arr, cv2.COLOR_YUV2BGR_NV21)


def get_android_camera_rotation(index: int = 0) -> int:
    """Clockwise degrees to rotate a camera frame for upright display."""
    try:
        from android import mActivity
        from jnius import autoclass
    except ImportError:
        return 90

    try:
        Camera = autoclass("android.hardware.Camera")
        CameraInfo = autoclass("android.hardware.Camera$CameraInfo")
        Context = autoclass("android.content.Context")

        info = CameraInfo()
        Camera.getCameraInfo(index, info)
        sensor_orientation = int(info.orientation)

        window_manager = mActivity.getSystemService(Context.WINDOW_SERVICE)
        display_rotation = int(window_manager.getDefaultDisplay().getRotation())
        display_degrees = display_rotation * 90

        if info.facing == CameraInfo.CAMERA_FACING_FRONT:
            degrees = (sensor_orientation + display_degrees) % 360
            return (360 - degrees) % 360
        degrees = (sensor_orientation - display_degrees + 360) % 360
        return degrees
    except Exception:
        logging.exception("Failed to read Android camera rotation; using 90°")
        return 90


def rotate_bgr(frame: np.ndarray, degrees: int) -> np.ndarray:
    if degrees == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if degrees == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if degrees == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


def bgr_to_preview_texture(frame: np.ndarray, *, android: bool) -> Texture:
    if android:
        display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        colorfmt = "rgb"
    else:
        display = frame
        colorfmt = "bgr"
    buffer = cv2.flip(display, 0).tobytes()
    texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt=colorfmt)
    texture.blit_buffer(buffer, colorfmt=colorfmt, bufferfmt="ubyte")
    return texture
