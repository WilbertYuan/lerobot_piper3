"""Real-time curve display widget (minimal implementation).

Uses a simple matplotlib-free approach with QPainter for M2.
Can be upgraded to pyqtgraph in later milestones.
"""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


COLORS = [
    QColor("#1f77b4"), QColor("#ff7f0e"), QColor("#2ca02c"),
    QColor("#d62728"), QColor("#9467bd"), QColor("#8c564b"),
    QColor("#e377c2"), QColor("#7f7f7f"), QColor("#bcbd22"),
    QColor("#17becf"),
]


class CurveWidget(QWidget):
    """Displays multiple named time-series as colored line curves."""

    def __init__(self, max_points: int = 200, parent: QWidget | None = None):
        super().__init__(parent)
        self._data: dict[str, deque[float]] = {}
        self._max_points = max_points
        self._series_order: list[str] = []
        self.setMinimumHeight(120)
        self.setStyleSheet("background-color: #111; border: 1px solid #333;")

    def add_data(self, series: dict[str, float]) -> None:
        """Append one data point per series."""
        for name, value in series.items():
            if name not in self._data:
                self._data[name] = deque(maxlen=self._max_points)
                self._series_order.append(name)
            self._data[name].append(value)
        self.update()

    def clear_data(self):
        self._data.clear()
        self._series_order.clear()

    def paintEvent(self, event):
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 4

        # Find global y range
        all_vals = [v for d in self._data.values() for v in d]
        if not all_vals:
            return
        ymin, ymax = min(all_vals), max(all_vals)
        if ymin == ymax:
            ymin -= 1
            ymax += 1

        for i, name in enumerate(self._series_order):
            pts = list(self._data[name])
            if len(pts) < 2:
                continue
            color = COLORS[i % len(COLORS)]
            pen = QPen(color, 1.5)
            p.setPen(pen)
            n = len(pts)
            for j in range(1, n):
                x1 = margin + (j - 1) / max(1, n - 1) * (w - 2 * margin)
                x2 = margin + j / max(1, n - 1) * (w - 2 * margin)
                y1 = h - margin - (pts[j - 1] - ymin) / (ymax - ymin) * (h - 2 * margin)
                y2 = h - margin - (pts[j] - ymin) / (ymax - ymin) * (h - 2 * margin)
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Legend
        p.setPen(Qt.GlobalColor.white)
        p.setFont(p.font())
        y_off = 12
        for i, name in enumerate(self._series_order):
            color = COLORS[i % len(COLORS)]
            p.setPen(QPen(color))
            p.drawText(8, y_off, name)
            y_off += 14

        p.end()
