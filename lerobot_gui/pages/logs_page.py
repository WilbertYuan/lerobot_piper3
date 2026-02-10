"""Logs page — unified log panel."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from lerobot_gui.widgets.log_viewer import LogViewer


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer)
