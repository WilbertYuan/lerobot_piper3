"""Devices page — robot type selection, dynamic form, connect/disconnect, status."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.adapters.registry import AdapterRegistry
from lerobot_gui.adapters.robots.generic_adapter import GenericRobotAdapter
from lerobot_gui.schemas import SchemaLoader
from lerobot_gui.services.config_store import ConfigStore
from lerobot_gui.services.task_manager import TaskManager
from lerobot_gui.widgets.dynamic_form import DynamicFormWidget

logger = logging.getLogger(__name__)


class DevicesPage(QWidget):
    def __init__(
        self,
        schema_loader: SchemaLoader,
        adapter_registry: AdapterRegistry,
        task_manager: TaskManager,
        config_store: ConfigStore,
        parent=None,
    ):
        super().__init__(parent)
        self._schemas = schema_loader
        self._registry = adapter_registry
        self._tasks = task_manager
        self._config_store = config_store
        self._current_adapter = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top bar
        top = QHBoxLayout()
        top.addWidget(QLabel("Robot Type:"))
        self._type_combo = QComboBox()
        for s in self._schemas.list_schemas("robot"):
            self._type_combo.addItem(f"{s.display_name} ({s.device_type})", s.device_type)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        top.addWidget(self._type_combo, 1)

        # Profile management
        self._profile_combo = QComboBox()
        self._profile_combo.setEditable(True)
        self._profile_combo.setPlaceholderText("Profile name...")
        self._profile_combo.setMinimumWidth(200)
        top.addWidget(self._profile_combo)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._save_profile)
        top.addWidget(btn_save)
        btn_load = QPushButton("Load")
        btn_load.clicked.connect(self._load_profile)
        top.addWidget(btn_load)

        layout.addLayout(top)

        # Splitter: form | status
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: dynamic form
        self._form = DynamicFormWidget()
        splitter.addWidget(self._form)

        # Right: controls + diagnostics + state
        right = QWidget()
        rl = QVBoxLayout(right)

        ctrl_group = QGroupBox("Control")
        cl = QVBoxLayout()
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setStyleSheet(
            "font-size: 14px; padding: 8px; background-color: #228B22; color: white;"
        )
        self._connect_btn.clicked.connect(self._on_connect)
        cl.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        cl.addWidget(self._disconnect_btn)

        self._status_label = QLabel("Status: Disconnected")
        self._status_label.setStyleSheet("font-size: 13px; padding: 4px;")
        cl.addWidget(self._status_label)
        ctrl_group.setLayout(cl)
        rl.addWidget(ctrl_group)

        diag_group = QGroupBox("Diagnostics")
        dl = QVBoxLayout()
        self._diag_text = QTextEdit()
        self._diag_text.setReadOnly(True)
        self._diag_text.setMaximumHeight(160)
        dl.addWidget(self._diag_text)
        diag_group.setLayout(dl)
        rl.addWidget(diag_group)

        state_group = QGroupBox("Current State")
        sl = QVBoxLayout()
        self._state_text = QTextEdit()
        self._state_text.setReadOnly(True)
        sl.addWidget(self._state_text)
        state_group.setLayout(sl)
        rl.addWidget(state_group)

        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([550, 400])
        layout.addWidget(splitter)

        # Init
        if self._type_combo.count() > 0:
            self._on_type_changed(0)

        # Polling timer for state display
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_state)

    def _on_type_changed(self, _index: int):
        dtype = self._type_combo.currentData()
        schema = self._schemas.get(dtype)
        self._form.set_schema(schema)
        # Refresh profiles
        self._profile_combo.clear()
        for p in self._config_store.list_profiles():
            if p.startswith(f"robot_{dtype}"):
                self._profile_combo.addItem(p)

    def _on_connect(self):
        dtype = self._type_combo.currentData()
        params = self._form.get_values()
        params["_robot_type"] = dtype

        reply = QMessageBox.question(
            self,
            "Confirm Connect",
            f"Connect to {dtype}?\nThis will enable motors.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        adapter_cls = self._registry.get_robot_adapter(dtype) or GenericRobotAdapter
        self._current_adapter = adapter_cls()
        self._connect_btn.setEnabled(False)
        self._status_label.setText("Status: Connecting...")
        self._status_label.setStyleSheet("color: #ffaa00; font-size: 13px;")

        def do_connect():
            self._current_adapter.connect(params)

        task = self._tasks.submit("robot_connect", do_connect)
        task.signals.finished.connect(self._on_connected)
        task.signals.error.connect(self._on_connect_error)

    def _on_connected(self, _task_id, _result):
        self._status_label.setText("Status: Connected")
        self._status_label.setStyleSheet("color: #44ff44; font-size: 13px;")
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)
        self._poll_timer.start(200)
        logger.info("Robot connected successfully")

    def _on_connect_error(self, _task_id, tb):
        self._status_label.setText("Status: Connection Failed")
        self._status_label.setStyleSheet("color: #ff4444; font-size: 13px;")
        self._connect_btn.setEnabled(True)
        self._diag_text.setPlainText(tb)
        logger.error(f"Connection failed:\n{tb}")

    def _on_disconnect(self):
        self._poll_timer.stop()
        if self._current_adapter:
            self._tasks.submit("robot_disconnect", self._current_adapter.disconnect)
        self._status_label.setText("Status: Disconnected")
        self._status_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self._state_text.clear()

    def _poll_state(self):
        if self._current_adapter and self._current_adapter.is_connected:
            try:
                state = self._current_adapter.get_state()
                lines = [f"{k}: {v:.4f}" for k, v in state.items()]
                self._state_text.setPlainText("\n".join(lines))
                diag = self._current_adapter.get_diagnostics()
                diag_lines = [f"{k}: {v}" for k, v in diag.items()]
                self._diag_text.setPlainText("\n".join(diag_lines))
            except Exception as e:
                self._state_text.setPlainText(f"Error: {e}")

    def _save_profile(self):
        name = self._profile_combo.currentText().strip()
        if not name:
            name = f"robot_{self._type_combo.currentData()}_default"
        data = self._form.get_values()
        data["_robot_type"] = self._type_combo.currentData()
        self._config_store.save_profile(name, data)
        logger.info(f"Profile saved: {name}")
        if self._profile_combo.findText(name) < 0:
            self._profile_combo.addItem(name)

    def _load_profile(self):
        name = self._profile_combo.currentText().strip()
        if not name:
            return
        try:
            data = self._config_store.load_profile(name)
            rt = data.pop("_robot_type", None)
            data.pop("_meta", None)
            if rt:
                idx = self._type_combo.findData(rt)
                if idx >= 0:
                    self._type_combo.setCurrentIndex(idx)
            self._form.set_values(data)
            logger.info(f"Profile loaded: {name}")
        except FileNotFoundError:
            logger.warning(f"Profile not found: {name}")

    def get_current_adapter(self):
        """Called by other pages (teleop, record) to get the connected robot."""
        return self._current_adapter
