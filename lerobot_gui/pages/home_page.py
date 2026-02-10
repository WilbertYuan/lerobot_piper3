"""Home page — project selection, environment check, recent projects."""

from __future__ import annotations

import sys
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.services.config_store import ConfigStore

logger = logging.getLogger(__name__)


class HomePage(QWidget):
    def __init__(self, config_store: ConfigStore, parent=None):
        super().__init__(parent)
        self._config_store = config_store
        self._setup_ui()
        self._refresh_recents()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Visual-Lerobot")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "LeRobot Desktop GUI — Robot Control & Learning Workstation"
        )
        subtitle.setStyleSheet("font-size: 14px; color: #888; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Working directory
        wd_group = QGroupBox("Working Directory")
        wd_layout = QHBoxLayout()
        self._wd_label = QLabel("Not selected")
        wd_layout.addWidget(self._wd_label, 1)
        btn = QPushButton("Browse...")
        btn.clicked.connect(self._browse_wd)
        wd_layout.addWidget(btn)
        wd_group.setLayout(wd_layout)
        layout.addWidget(wd_group)

        # Recent projects
        recent_group = QGroupBox("Recent Projects")
        rl = QVBoxLayout()
        self._recent_list = QListWidget()
        rl.addWidget(self._recent_list)
        recent_group.setLayout(rl)
        layout.addWidget(recent_group)

        # Environment check
        env_group = QGroupBox("Environment Check")
        el = QVBoxLayout()
        self._env_text = QTextEdit()
        self._env_text.setReadOnly(True)
        self._env_text.setMaximumHeight(200)
        el.addWidget(self._env_text)
        btn_check = QPushButton("Run Check")
        btn_check.clicked.connect(self._run_env_check)
        el.addWidget(btn_check)
        env_group.setLayout(el)
        layout.addWidget(env_group)
        layout.addStretch()

    def _browse_wd(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self._wd_label.setText(path)
            self._config_store.add_recent_project(path)
            self._refresh_recents()

    def _refresh_recents(self):
        self._recent_list.clear()
        for r in self._config_store.get_recent_projects():
            self._recent_list.addItem(f"{r['name']}  —  {r['path']}")

    def _run_env_check(self):
        lines = []
        lines.append(f"Python: {sys.version}")
        lines.append(f"Platform: {sys.platform}")

        for pkg in [
            "lerobot",
            "PySide6",
            "torch",
            "numpy",
            "piper_sdk",
            "pyserial",
            "cv2",
            "yaml",
        ]:
            try:
                mod = __import__(pkg)
                ver = getattr(mod, "__version__", "OK")
                lines.append(f"  [OK]   {pkg} == {ver}")
            except ImportError:
                lines.append(f"  [MISS] {pkg} — not installed")

        self._env_text.setPlainText("\n".join(lines))
        logger.info("Environment check completed")
