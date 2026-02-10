"""Emergency stop button widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QSizePolicy


class EStopButton(QPushButton):
    """Big red emergency stop button for the bottom status bar."""

    e_stop_triggered = Signal()
    e_stop_released = Signal()

    def __init__(self, parent=None):
        super().__init__("E-STOP", parent)
        self._active = False
        self.setCheckable(True)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._update_style()
        self.clicked.connect(self._on_click)

    def _on_click(self):
        self._active = self.isChecked()
        self._update_style()
        if self._active:
            self.e_stop_triggered.emit()
        else:
            self.e_stop_released.emit()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #cc0000; color: white;"
                "  font-size: 18px; font-weight: bold;"
                "  border: 3px solid #880000; border-radius: 8px; padding: 8px;"
                "}"
            )
            self.setText("E-STOP [ACTIVE] — Click to Release")
        else:
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #ff4444; color: white;"
                "  font-size: 16px; font-weight: bold;"
                "  border: 2px solid #cc0000; border-radius: 8px; padding: 8px;"
                "}"
                "QPushButton:hover { background-color: #ff0000; }"
            )
            self.setText("E-STOP")
