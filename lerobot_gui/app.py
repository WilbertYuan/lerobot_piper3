"""Visual-Lerobot GUI — application entry point.

Usage:
    python -m lerobot_gui.app
"""

import sys
import logging

from PySide6.QtWidgets import QApplication

from lerobot_gui.main_window import MainWindow


DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: "Segoe UI", "SF Pro", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton {
    background-color: #3a3a3a;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 16px;
    color: #ddd;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QPushButton:pressed {
    background-color: #555;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 8px;
    color: #ddd;
    min-height: 22px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QTextEdit, QPlainTextEdit {
    background-color: #1a1a1a;
    border: 1px solid #3a3a3a;
    color: #ccc;
}
QListWidget {
    background-color: #2b2b2b;
    border: none;
}
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 10px;
}
QScrollBar::handle:vertical {
    background-color: #555;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background-color: #555;
    border-radius: 5px;
    min-width: 20px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QToolTip {
    background-color: #333;
    color: #eee;
    border: 1px solid #555;
    padding: 4px;
}
"""


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("Visual-Lerobot")
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
