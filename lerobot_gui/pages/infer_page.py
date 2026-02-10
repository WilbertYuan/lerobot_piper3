"""Inference page — load checkpoint, connect robot, run rollout / eval."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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

logger = logging.getLogger(__name__)


class InferPage(QWidget):
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

        # ---- Checkpoint ----
        ckpt_group = QGroupBox("Model / Checkpoint")
        cf = QFormLayout()

        self._policy_path = QLineEdit()
        self._policy_path.setPlaceholderText("outputs/train/act_so100_test/checkpoints/last/pretrained_model")
        ckpt_row = QHBoxLayout()
        ckpt_row.addWidget(self._policy_path)
        btn_browse = QPushButton("...")
        btn_browse.clicked.connect(self._browse_ckpt)
        ckpt_row.addWidget(btn_browse)
        cf.addRow("--policy.path:", ckpt_row)

        self._policy_type = QComboBox()
        self._policy_type.setEditable(True)
        self._policy_type.addItems(["act", "diffusion", "pi0", "pi0fast", "tdmpc", "vqbet", "smolvla"])
        cf.addRow("--policy.type:", self._policy_type)

        ckpt_group.setLayout(cf)
        cl.addWidget(ckpt_group)

        # ---- Robot config ----
        robot_group = QGroupBox("Robot / Environment")
        rf = QFormLayout()

        self._robot_type = QComboBox()
        self._robot_type.setEditable(True)
        self._robot_type.addItems([
            "piper_follower", "so100_follower", "koch_follower",
            "lekiwi", "unitree_g1", "reachy2",
        ])
        rf.addRow("--robot.type:", self._robot_type)

        self._robot_port = QLineEdit()
        self._robot_port.setPlaceholderText("Optional: /dev/ttyACM0")
        rf.addRow("--robot.port:", self._robot_port)

        self._robot_can = QLineEdit()
        self._robot_can.setPlaceholderText("Optional: can_slave1")
        rf.addRow("--robot.motors.can_name:", self._robot_can)

        robot_group.setLayout(rf)
        cl.addWidget(robot_group)

        # ---- Eval / Record (rollout) ----
        eval_group = QGroupBox("Evaluation Settings")
        ef = QFormLayout()

        self._mode = QComboBox()
        self._mode.addItems(["record (rollout)", "eval"])
        ef.addRow("Mode:", self._mode)

        self._dataset_repo = QLineEdit()
        self._dataset_repo.setPlaceholderText("user/eval_dataset_name")
        ef.addRow("--dataset.repo_id:", self._dataset_repo)

        self._task = QLineEdit()
        self._task.setPlaceholderText("Task description for rollout")
        ef.addRow("--task:", self._task)

        self._num_episodes = QSpinBox()
        self._num_episodes.setRange(1, 1000)
        self._num_episodes.setValue(10)
        ef.addRow("Num episodes:", self._num_episodes)

        self._fps = QSpinBox()
        self._fps.setRange(1, 120)
        self._fps.setValue(30)
        ef.addRow("--fps:", self._fps)

        self._push_to_hub = QCheckBox()
        ef.addRow("Push to Hub:", self._push_to_hub)

        self._extra_args = QLineEdit()
        self._extra_args.setPlaceholderText("Additional CLI arguments")
        ef.addRow("Extra args:", self._extra_args)

        eval_group.setLayout(ef)
        cl.addWidget(eval_group)
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Controls
        ctrl = QHBoxLayout()
        self._start_btn = QPushButton("Run Inference")
        self._start_btn.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #9C27B0; color: white;"
        )
        self._start_btn.clicked.connect(self._on_start)
        ctrl.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        ctrl.addWidget(self._stop_btn)

        self._copy_btn = QPushButton("Copy Command")
        self._copy_btn.clicked.connect(self._copy_cmd)
        ctrl.addWidget(self._copy_btn)
        layout.addLayout(ctrl)

        self._cmd_label = QLabel("")
        self._cmd_label.setWordWrap(True)
        self._cmd_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._cmd_label)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(250)
        self._output.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self._output)

    def _browse_ckpt(self):
        path = QFileDialog.getExistingDirectory(self, "Select Checkpoint Directory")
        if path:
            self._policy_path.setText(path)

    def _build_command(self) -> list[str]:
        mode = self._mode.currentText()
        if "record" in mode:
            cmd = ["lerobot-record"]
            cmd += ["--robot.type", self._robot_type.currentText()]
            cmd += ["--policy.path", self._policy_path.text().strip()]
            if self._dataset_repo.text().strip():
                cmd += ["--dataset.repo_id", self._dataset_repo.text().strip()]
            if self._task.text().strip():
                cmd += ["--task", self._task.text().strip()]
            cmd += ["--dataset.num_episodes", str(self._num_episodes.value())]
            cmd += ["--fps", str(self._fps.value())]
            if self._push_to_hub.isChecked():
                cmd += ["--dataset.push_to_hub", "1"]
        else:
            cmd = ["lerobot-eval"]
            cmd += ["--policy.path", self._policy_path.text().strip()]
            if self._dataset_repo.text().strip():
                cmd += ["--dataset.repo_id", self._dataset_repo.text().strip()]
            cmd += ["--eval.n_episodes", str(self._num_episodes.value())]

        # Robot-specific
        if self._robot_port.text().strip():
            cmd += ["--robot.port", self._robot_port.text().strip()]
        if self._robot_can.text().strip():
            cmd += ["--robot.motors.can_name", self._robot_can.text().strip()]

        extra = self._extra_args.text().strip()
        if extra:
            cmd += extra.split()
        return cmd

    def _on_start(self):
        cmd = self._build_command()
        cmd_str = " ".join(cmd)
        self._cmd_label.setText(f"$ {cmd_str}")
        self._output.clear()
        self._output.appendPlainText(f"Running: {cmd_str}\n")
        if self._proc_mgr:
            self._proc_mgr.output_line.connect(self._on_output)
            self._proc_mgr.highlight_line.connect(self._on_highlight)
            self._proc_mgr.process_finished.connect(self._on_finished)
            self._proc_mgr.start_process("infer", cmd, config_snapshot={
                "policy_path": self._policy_path.text(),
                "robot_type": self._robot_type.currentText(),
                "mode": self._mode.currentText(),
            })
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        logger.info(f"Inference started: {cmd_str}")

    def _on_stop(self):
        if self._proc_mgr:
            self._proc_mgr.kill_process("infer")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_output(self, tid, line):
        if tid == "infer":
            self._output.appendPlainText(line)

    def _on_highlight(self, tid, line):
        if tid == "infer":
            self._output.appendPlainText(f">>> {line}")

    def _on_finished(self, tid, code):
        if tid == "infer":
            self._output.appendPlainText(f"\n--- Inference finished (exit: {code}) ---")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

    def _copy_cmd(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(" ".join(self._build_command()))
