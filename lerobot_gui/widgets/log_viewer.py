"""Log viewer widget with filtering, search, and copy support."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

LEVEL_COLORS = {
    "DEBUG": QColor("#888888"),
    "INFO": QColor("#cccccc"),
    "WARNING": QColor("#ffaa00"),
    "ERROR": QColor("#ff4444"),
    "CRITICAL": QColor("#ff0000"),
}


class LogViewer(QWidget):
    """Unified log viewer with level filtering and search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self._level_filter = QComboBox()
        self._level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        self._level_filter.setCurrentText("ALL")
        toolbar.addWidget(self._level_filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search logs...")
        toolbar.addWidget(self._search, 1)

        self._copy_btn = QPushButton("Copy All")
        self._copy_btn.clicked.connect(self._copy_all)
        toolbar.addWidget(self._copy_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(self._clear_btn)

        layout.addLayout(toolbar)

        # Log text area
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(10000)
        self._text.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self._text)

        self._all_lines: list[tuple[str, str, str]] = []

    @Slot(str, str, str)
    def append_log(self, level: str, timestamp: str, message: str):
        """Append a log line. Connected to LogSignalEmitter.log_record."""
        self._all_lines.append((level, timestamp, message))

        # Filter check
        filter_level = self._level_filter.currentText()
        if filter_level != "ALL" and level != filter_level:
            return

        search = self._search.text().lower()
        if search and search not in message.lower():
            return

        color = LEVEL_COLORS.get(level, QColor("#cccccc"))
        fmt = QTextCharFormat()
        fmt.setForeground(color)

        cursor = self._text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(f"[{timestamp}] {level:8s} {message}\n", fmt)
        self._text.ensureCursorVisible()

    def _copy_all(self):
        QApplication.clipboard().setText(self._text.toPlainText())

    def _clear(self):
        self._text.clear()
        self._all_lines.clear()
