"""Video display widget — renders numpy frames in a QLabel."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class VideoWidget(QLabel):
    """Displays video frames from numpy arrays (HWC, RGB or BGR)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #111; border: 1px solid #333;")
        self.setText("No video feed")

    def update_frame(self, frame: np.ndarray) -> None:
        """Display a numpy frame (H, W, 3) as RGB."""
        if frame is None or frame.size == 0:
            return
        h, w = frame.shape[:2]
        if frame.ndim == 2:
            # Grayscale
            qimg = QImage(frame.data, w, h, w, QImage.Format.Format_Grayscale8)
        elif frame.shape[2] == 3:
            # RGB
            bytes_per_line = 3 * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        elif frame.shape[2] == 4:
            # RGBA
            bytes_per_line = 4 * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
        else:
            return

        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)
