"""Intel RealSense camera adapter — wraps lerobot.cameras.realsense."""

from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np

from .base_adapter import BaseCameraAdapter

logger = logging.getLogger(__name__)


class RealSenseCameraAdapter(BaseCameraAdapter):
    def __init__(self):
        super().__init__()
        self._camera = None
        self._lock = threading.Lock()

    def open(self, params: dict[str, Any]) -> None:
        with self._lock:
            from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
            from lerobot.cameras.realsense.camera_realsense import RealSenseCamera

            config = RealSenseCameraConfig(
                serial_number_or_name=str(params.get("serial_number_or_name", "")),
                fps=int(params.get("fps", 30)),
                width=int(params.get("width", 640)),
                height=int(params.get("height", 480)),
                use_depth=bool(params.get("use_depth", False)),
                color_mode=params.get("color_mode", "rgb"),
            )
            self._camera = RealSenseCamera(config)
            self._camera.connect()
            logger.info(f"RealSense camera opened (sn={config.serial_number_or_name})")

    def close(self) -> None:
        with self._lock:
            if self._camera:
                try:
                    self._camera.disconnect()
                except Exception as e:
                    logger.error(f"RealSense close error: {e}")
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
                logger.debug(f"RealSense frame error: {e}")
                return None

    def get_params(self) -> dict[str, Any]:
        if self._camera:
            return {
                "type": "intelrealsense",
                "serial_number_or_name": self._camera.config.serial_number_or_name,
                "width": self._camera.config.width,
                "height": self._camera.config.height,
                "fps": self._camera.config.fps,
                "use_depth": self._camera.config.use_depth,
            }
        return {}
