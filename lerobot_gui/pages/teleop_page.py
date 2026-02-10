"""Teleop page — manual control with safety filter, E-STOP, real-time curves."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.schemas import SchemaLoader
from lerobot_gui.services.safety_filter import SafetyFilter
from lerobot_gui.widgets.curve_widget import CurveWidget
from lerobot_gui.widgets.dynamic_form import DynamicFormWidget

logger = logging.getLogger(__name__)


class TeleopPage(QWidget):
    """
    Teleop page:
    - Select teleoperator type + params
    - Connect teleoperator
    - Read teleop state → SafetyFilter → send to robot adapter
    - Real-time joint/action curves
    - E-STOP integration
    """

    def __init__(
        self,
        schema_loader: SchemaLoader | None = None,
        safety_filter: SafetyFilter | None = None,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self._schemas = schema_loader
        self._safety = safety_filter or SafetyFilter()
        self._robot_adapter = None  # Set externally from DevicesPage
        self._teleop_adapter = None
        self._running = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Teleop type selection
        top = QHBoxLayout()
        top.addWidget(QLabel("Teleoperator:"))
        self._type_combo = QComboBox()
        if self._schemas:
            for s in self._schemas.list_schemas("teleoperator"):
                self._type_combo.addItem(f"{s.display_name}", s.device_type)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        top.addWidget(self._type_combo, 1)
        layout.addLayout(top)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: teleop config + control panel
        left = QWidget()
        ll = QVBoxLayout(left)

        self._form = DynamicFormWidget()
        ll.addWidget(self._form, 1)

        # Safety settings
        safety_group = QGroupBox("Safety Filter")
        sf_layout = QVBoxLayout()

        hl1 = QHBoxLayout()
        hl1.addWidget(QLabel("Max Velocity:"))
        self._max_vel = QDoubleSpinBox()
        self._max_vel.setRange(0.01, 10.0)
        self._max_vel.setValue(0.5)
        self._max_vel.setSingleStep(0.05)
        self._max_vel.valueChanged.connect(self._update_safety)
        hl1.addWidget(self._max_vel)

        hl1.addWidget(QLabel("Deadzone:"))
        self._deadzone = QDoubleSpinBox()
        self._deadzone.setRange(0.0, 1.0)
        self._deadzone.setValue(0.001)
        self._deadzone.setDecimals(4)
        self._deadzone.valueChanged.connect(self._update_safety)
        hl1.addWidget(self._deadzone)

        hl1.addWidget(QLabel("Timeout (ms):"))
        self._timeout = QDoubleSpinBox()
        self._timeout.setRange(100, 5000)
        self._timeout.setValue(500)
        self._timeout.valueChanged.connect(self._update_safety)
        hl1.addWidget(self._timeout)
        sf_layout.addLayout(hl1)

        self._filter_enabled = QCheckBox("Enable Safety Filter")
        self._filter_enabled.setChecked(True)
        sf_layout.addWidget(self._filter_enabled)

        safety_group.setLayout(sf_layout)
        ll.addWidget(safety_group)

        # Control buttons
        ctrl_group = QGroupBox("Teleop Control")
        cl = QVBoxLayout()

        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Start Teleop")
        self._start_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #228B22; color: white;")
        self._start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop Teleop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        btn_row.addWidget(self._stop_btn)
        cl.addLayout(btn_row)

        self._status_label = QLabel("Status: Idle")
        self._status_label.setStyleSheet("font-size: 13px;")
        cl.addWidget(self._status_label)

        ctrl_group.setLayout(cl)
        ll.addWidget(ctrl_group)

        splitter.addWidget(left)

        # Right: curves + state
        right = QWidget()
        rl = QVBoxLayout(right)

        self._curve = CurveWidget(max_points=300)
        self._curve.setMinimumHeight(200)
        rl.addWidget(self._curve, 2)

        state_group = QGroupBox("Current Action / State")
        stl = QVBoxLayout()
        self._action_text = QTextEdit()
        self._action_text.setReadOnly(True)
        self._action_text.setMaximumHeight(200)
        stl.addWidget(self._action_text)
        state_group.setLayout(stl)
        rl.addWidget(state_group, 1)

        splitter.addWidget(right)
        splitter.setSizes([450, 500])
        layout.addWidget(splitter)

        # Polling timer
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_teleop)

        if self._type_combo.count() > 0:
            self._on_type_changed(0)

    def set_robot_adapter(self, adapter):
        """Called by MainWindow when DevicesPage connects a robot."""
        self._robot_adapter = adapter

    def _on_type_changed(self, _index):
        dtype = self._type_combo.currentData()
        if self._schemas:
            schema = self._schemas.get(dtype)
            self._form.set_schema(schema)

    def _update_safety(self):
        self._safety.max_velocity = self._max_vel.value()
        self._safety.deadzone = self._deadzone.value()
        self._safety.timeout_ms = self._timeout.value()

    def _on_start(self):
        if self._robot_adapter is None or not self._robot_adapter.is_connected:
            self._status_label.setText("Error: No robot connected! Go to Devices page first.")
            self._status_label.setStyleSheet("color: #ff4444;")
            return

        self._running = True
        self._safety.reset()
        self._curve.clear_data()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_label.setText("Status: Running")
        self._status_label.setStyleSheet("color: #44ff44;")
        self._poll_timer.start(50)  # 20Hz
        logger.info("Teleop started")

    def _on_stop(self):
        self._running = False
        self._poll_timer.stop()
        if self._robot_adapter and self._robot_adapter.is_connected:
            try:
                self._robot_adapter.stop()
            except Exception as e:
                logger.error(f"Stop error: {e}")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: Stopped")
        self._status_label.setStyleSheet("color: #cccccc;")
        logger.info("Teleop stopped")

    def _poll_teleop(self):
        """Read state from robot, display in curves. Teleop input not yet wired."""
        if not self._running or not self._robot_adapter:
            return

        # Check safety timeout
        if self._safety.check_timeout():
            logger.warning("Teleop input timeout — auto-stopping")
            self._on_stop()
            return

        try:
            state = self._robot_adapter.get_state()
            if state:
                self._curve.add_data(state)
                lines = [f"{k}: {v:.4f}" for k, v in state.items()]
                self._action_text.setPlainText("\n".join(lines))
        except Exception as e:
            logger.error(f"Teleop poll error: {e}")
