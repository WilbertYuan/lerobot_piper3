"""Record page — configure and launch data recording via lerobot-record CLI."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.services.subprocess_manager import SubprocessManager
from lerobot_gui.widgets.log_viewer import LogViewer

logger = logging.getLogger(__name__)


class RecordPage(QWidget):
    """
    Record/data collection page.

    Builds the lerobot-record CLI command from form fields and launches
    it as a subprocess, streaming output in real time.
    """

    def __init__(
        self,
        subprocess_mgr: SubprocessManager | None = None,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self._proc_mgr = subprocess_mgr
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)

        # ---- Required parameters ----
        req_group = QGroupBox("Required Parameters")
        form = QFormLayout()

        self._robot_type = QComboBox()
        self._robot_type.setEditable(True)
        self._robot_type.addItems([
            "piper_follower", "so100_follower", "so101_follower",
            "koch_follower", "lekiwi", "lekiwi_client",
            "unitree_g1", "openarm_follower", "reachy2",
        ])
        form.addRow("--robot.type:", self._robot_type)

        self._teleop_type = QComboBox()
        self._teleop_type.setEditable(True)
        self._teleop_type.addItems([
            "piper_leader", "so100_leader", "so101_leader",
            "koch_leader", "keyboard", "gamepad", "phone",
        ])
        form.addRow("--teleop.type:", self._teleop_type)

        self._dataset_repo = QLineEdit()
        self._dataset_repo.setPlaceholderText("user/dataset_name")
        form.addRow("--dataset.repo_id:", self._dataset_repo)

        self._task = QLineEdit()
        self._task.setPlaceholderText("e.g. Pick the Lego block and put it on the plate")
        form.addRow("--task:", self._task)

        req_group.setLayout(form)
        cl.addWidget(req_group)

        # ---- Episode settings ----
        ep_group = QGroupBox("Episode Settings")
        ep_form = QFormLayout()

        self._num_episodes = QSpinBox()
        self._num_episodes.setRange(1, 10000)
        self._num_episodes.setValue(50)
        ep_form.addRow("--dataset.num_episodes:", self._num_episodes)

        self._fps = QSpinBox()
        self._fps.setRange(1, 120)
        self._fps.setValue(30)
        ep_form.addRow("--fps:", self._fps)

        self._warmup = QSpinBox()
        self._warmup.setRange(0, 30)
        self._warmup.setValue(5)
        ep_form.addRow("--warmup_time_s:", self._warmup)

        self._episode_time = QSpinBox()
        self._episode_time.setRange(1, 600)
        self._episode_time.setValue(30)
        ep_form.addRow("--episode_time_s:", self._episode_time)

        self._reset_time = QSpinBox()
        self._reset_time.setRange(0, 60)
        self._reset_time.setValue(5)
        ep_form.addRow("--reset_time_s:", self._reset_time)

        ep_group.setLayout(ep_form)
        cl.addWidget(ep_group)

        # ---- Robot-specific parameters ----
        robot_group = QGroupBox("Robot-Specific Parameters (optional)")
        rf = QFormLayout()

        self._robot_port = QLineEdit()
        self._robot_port.setPlaceholderText("/dev/ttyACM0 (serial robots)")
        rf.addRow("--robot.port:", self._robot_port)

        self._robot_can = QLineEdit()
        self._robot_can.setPlaceholderText("can_slave1 (Piper)")
        rf.addRow("--robot.motors.can_name:", self._robot_can)

        self._teleop_port = QLineEdit()
        self._teleop_port.setPlaceholderText("/dev/ttyACM1 (serial leader)")
        rf.addRow("--teleop.port:", self._teleop_port)

        self._teleop_can = QLineEdit()
        self._teleop_can.setPlaceholderText("can_master1 (Piper leader)")
        rf.addRow("--teleop.motors.can_name:", self._teleop_can)

        robot_group.setLayout(rf)
        cl.addWidget(robot_group)

        # ---- Advanced options ----
        adv_group = QGroupBox("Advanced Options")
        adv_group.setCheckable(True)
        adv_group.setChecked(False)
        af = QFormLayout()

        self._single_task = QCheckBox()
        self._single_task.setChecked(True)
        af.addRow("--single_task:", self._single_task)

        self._push_to_hub = QCheckBox()
        self._push_to_hub.setChecked(True)
        af.addRow("--dataset.push_to_hub:", self._push_to_hub)

        self._force_override = QCheckBox()
        af.addRow("--force_override:", self._force_override)

        self._resume = QCheckBox()
        af.addRow("--resume:", self._resume)

        self._extra_args = QLineEdit()
        self._extra_args.setPlaceholderText("Any additional CLI arguments")
        af.addRow("Extra args:", self._extra_args)

        adv_group.setLayout(af)
        cl.addWidget(adv_group)

        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ---- Controls ----
        ctrl_row = QHBoxLayout()
        self._start_btn = QPushButton("Start Recording")
        self._start_btn.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #228B22; color: white;"
        )
        self._start_btn.clicked.connect(self._on_start)
        ctrl_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        ctrl_row.addWidget(self._stop_btn)

        self._copy_btn = QPushButton("Copy Command")
        self._copy_btn.clicked.connect(self._copy_cmd)
        ctrl_row.addWidget(self._copy_btn)

        layout.addLayout(ctrl_row)

        # Command preview
        self._cmd_preview = QLabel("")
        self._cmd_preview.setWordWrap(True)
        self._cmd_preview.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        layout.addWidget(self._cmd_preview)

        # Output log
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(200)
        self._output.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self._output)

    def _build_command(self) -> list[str]:
        cmd = ["lerobot-record"]
        cmd += ["--robot.type", self._robot_type.currentText()]
        cmd += ["--teleop.type", self._teleop_type.currentText()]

        if self._dataset_repo.text().strip():
            cmd += ["--dataset.repo_id", self._dataset_repo.text().strip()]
        if self._task.text().strip():
            cmd += ["--task", self._task.text().strip()]
        cmd += ["--dataset.num_episodes", str(self._num_episodes.value())]
        cmd += ["--fps", str(self._fps.value())]
        cmd += ["--warmup_time_s", str(self._warmup.value())]
        cmd += ["--episode_time_s", str(self._episode_time.value())]
        cmd += ["--reset_time_s", str(self._reset_time.value())]

        # Robot-specific
        if self._robot_port.text().strip():
            cmd += ["--robot.port", self._robot_port.text().strip()]
        if self._robot_can.text().strip():
            cmd += ["--robot.motors.can_name", self._robot_can.text().strip()]
        if self._teleop_port.text().strip():
            cmd += ["--teleop.port", self._teleop_port.text().strip()]
        if self._teleop_can.text().strip():
            cmd += ["--teleop.motors.can_name", self._teleop_can.text().strip()]

        # Booleans
        if self._single_task.isChecked():
            cmd += ["--single_task", "1"]
        if self._push_to_hub.isChecked():
            cmd += ["--dataset.push_to_hub", "1"]
        if self._force_override.isChecked():
            cmd += ["--force_override", "1"]
        if self._resume.isChecked():
            cmd += ["--resume", "1"]

        extra = self._extra_args.text().strip()
        if extra:
            cmd += extra.split()

        return cmd

    def _on_start(self):
        cmd = self._build_command()
        cmd_str = " ".join(cmd)
        self._cmd_preview.setText(f"$ {cmd_str}")
        self._output.clear()
        self._output.appendPlainText(f"Running: {cmd_str}\n")

        if self._proc_mgr:
            self._proc_mgr.output_line.connect(self._on_output)
            self._proc_mgr.highlight_line.connect(self._on_highlight)
            self._proc_mgr.process_finished.connect(self._on_finished)
            self._proc_mgr.start_process("record", cmd, config_snapshot={
                "robot_type": self._robot_type.currentText(),
                "teleop_type": self._teleop_type.currentText(),
                "fps": self._fps.value(),
                "num_episodes": self._num_episodes.value(),
            })
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        logger.info(f"Recording started: {cmd_str}")

    def _on_stop(self):
        if self._proc_mgr:
            self._proc_mgr.kill_process("record")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_output(self, task_id: str, line: str):
        if task_id == "record":
            self._output.appendPlainText(line)

    def _on_highlight(self, task_id: str, line: str):
        if task_id == "record":
            self._output.appendPlainText(f">>> {line}")

    def _on_finished(self, task_id: str, code: int):
        if task_id == "record":
            self._output.appendPlainText(f"\n--- Process finished (exit code: {code}) ---")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

    def _copy_cmd(self):
        from PySide6.QtWidgets import QApplication
        cmd_str = " ".join(self._build_command())
        QApplication.clipboard().setText(cmd_str)
        self._cmd_preview.setText(f"Copied: {cmd_str}")
