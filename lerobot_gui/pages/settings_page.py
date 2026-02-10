"""Settings page — global preferences."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.services.config_store import ConfigStore


class SettingsPage(QWidget):
    def __init__(self, config_store: ConfigStore, parent=None):
        super().__init__(parent)
        self._store = config_store
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        gen = QGroupBox("General")
        form = QFormLayout()

        self._data_dir = QLineEdit()
        self._data_dir.setPlaceholderText("Default data storage directory")
        form.addRow("Data Directory:", self._data_dir)

        self._theme = QComboBox()
        self._theme.addItems(["System", "Dark", "Light"])
        form.addRow("Theme:", self._theme)

        self._confirm_danger = QCheckBox("Confirm dangerous operations")
        self._confirm_danger.setChecked(True)
        form.addRow("Safety:", self._confirm_danger)

        self._hf_user = QLineEdit()
        self._hf_user.setPlaceholderText("HuggingFace username")
        form.addRow("HF User:", self._hf_user)

        gen.setLayout(form)
        layout.addWidget(gen)

        btn = QPushButton("Save Settings")
        btn.clicked.connect(self._save)
        layout.addWidget(btn)

        self._status = QLabel("")
        layout.addWidget(self._status)
        layout.addStretch()

    def _save(self):
        self._store.save_settings(
            {
                "data_dir": self._data_dir.text(),
                "theme": self._theme.currentText(),
                "confirm_danger": self._confirm_danger.isChecked(),
                "hf_user": self._hf_user.text(),
            }
        )
        self._status.setText("Settings saved.")

    def _load(self):
        s = self._store.load_settings()
        self._data_dir.setText(s.get("data_dir", ""))
        idx = self._theme.findText(s.get("theme", "System"))
        if idx >= 0:
            self._theme.setCurrentIndex(idx)
        self._confirm_danger.setChecked(s.get("confirm_danger", True))
        self._hf_user.setText(s.get("hf_user", ""))
