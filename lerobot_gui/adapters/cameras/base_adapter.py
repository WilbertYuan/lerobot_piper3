"""Abstract base class for all camera adapters."""

from __future__ import annotations

import abc
import time
from typing import Any

import numpy as np


class BaseCameraAdapter(abc.ABC):
    """
    Stable interface between GUI and any camera backend.

    GUI code ONLY depends on this — never on concrete camera classes.
    """

    def __init__(self):
        self._fps_ts: list[float] = []

    @abc.abstractmethod
    def open(self, params: dict[str, Any]) -> None:
        """Open the camera with given parameters."""

    @abc.abstractmethod
    def close(self) -> None:
        """Close / release the camera."""

    @property
    @abc.abstractmethod
    def is_open(self) -> bool: ...

    @abc.abstractmethod
    def read_frame(self) -> np.ndarray | None:
        """Read a single frame as HWC RGB numpy array, or None."""

    @abc.abstractmethod
    def get_params(self) -> dict[str, Any]:
        """Return current camera parameters."""

    def fps_stats(self) -> dict[str, float]:
        """Return measured FPS statistics."""
        now = time.time()
        self._fps_ts = [t for t in self._fps_ts if now - t < 2.0]
        fps = len(self._fps_ts) / 2.0 if self._fps_ts else 0.0
        return {"measured_fps": round(fps, 1), "frame_count": len(self._fps_ts)}

    def _record_frame(self):
        self._fps_ts.append(time.time())
