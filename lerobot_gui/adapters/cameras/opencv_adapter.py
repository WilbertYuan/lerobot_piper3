"""OpenCV camera adapter — wraps lerobot.cameras.opencv."""

from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np

from .base_adapter import BaseCameraAdapter

logger = logging.getLogger(__name__)


class OpenCVCameraAdapter(BaseCameraAdapter):
    def __init__(self):
        super().__init__()
        self._camera = None
        self._lock = threading.Lock()

    def open(self, params: dict[str, Any]) -> None:
        with self._lock:
            from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
            from lerobot.cameras.opencv.camera_opencv import OpenCVCamera

            # Parse index_or_path (could be int or string)
            idx = params.get("index_or_path", 0)
            try:
                idx = int(idx)
            except (ValueError, TypeError):
                pass  # keep as string (path)

            config = OpenCVCameraConfig(
                index_or_path=idx,
                fps=int(params.get("fps", 30)),
                width=int(params.get("width", 640)),
                height=int(params.get("height", 480)),
                color_mode=params.get("color_mode", "rgb"),
            )

            rotation = params.get("rotation", "no_rotation")
            if rotation and rotation != "no_rotation":
                # Import rotation enum if available
                try:
                    from lerobot.cameras.configs import Cv2Rotation
                    rot_map = {"90": Cv2Rotation.ROTATE_90, "180": Cv2Rotation.ROTATE_180,
                               "270": Cv2Rotation.ROTATE_270}
                    if rotation in rot_map:
                        config.rotation = rot_map[rotation]
                except Exception:
                    pass

            self._camera = OpenCVCamera(config)
            self._camera.connect()
            logger.info(f"OpenCV camera opened (index={idx})")

    def close(self) -> None:
        with self._lock:
            if self._camera:
                try:
                    self._camera.disconnect()
                except Exception as e:
                    logger.error(f"Camera close error: {e}")
                finally:
                    self._camera = None

    @property
    def is_open(self) -> bool:
        return self._camera is not None and self._camera.is_connected

    def read_frame(self) -> np.ndarray | None:
        with self._lock:
            if not self._camera:
                return None
            try:
                frame = self._camera.read()
                self._record_frame()
                if isinstance(frame, np.ndarray):
                    return frame
                return None
            except Exception as e:
                logger.debug(f"Frame read error: {e}")
                return None

    def get_params(self) -> dict[str, Any]:
        if self._camera:
            return {
                "type": "opencv",
                "index": self._camera.config.index_or_path,
                "width": self._camera.config.width,
                "height": self._camera.config.height,
                "fps": self._camera.config.fps,
            }
        return {}
