"""Train page — configure and launch policy training via lerobot-train CLI."""

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

logger = logging.getLogger(__name__)


class TrainPage(QWidget):
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

        # ---- Policy / algorithm ----
        policy_group = QGroupBox("Policy Configuration")
        pf = QFormLayout()

        self._policy = QComboBox()
        self._policy.setEditable(True)
        self._policy.addItems([
            "act", "diffusion", "pi0", "pi0fast",
            "tdmpc", "vqbet", "smolvla",
        ])
        pf.addRow("--policy.type:", self._policy)

        self._dataset_repo = QLineEdit()
        self._dataset_repo.setPlaceholderText("user/dataset_name")
        pf.addRow("--dataset.repo_id:", self._dataset_repo)

        self._output_dir = QLineEdit()
        self._output_dir.setPlaceholderText("outputs/train/act_so100_test")
        pf.addRow("--output_dir:", self._output_dir)

        policy_group.setLayout(pf)
        cl.addWidget(policy_group)

        # ---- Training parameters ----
        train_group = QGroupBox("Training Parameters")
        tf = QFormLayout()

        self._device = QComboBox()
        self._device.addItems(["cuda", "cpu", "mps"])
        tf.addRow("--device:", self._device)

        self._steps = QSpinBox()
        self._steps.setRange(100, 10_000_000)
        self._steps.setValue(80_000)
        self._steps.setSingleStep(1000)
        tf.addRow("--training.num_steps (steps):", self._steps)

        self._batch_size = QSpinBox()
        self._batch_size.setRange(1, 256)
        self._batch_size.setValue(8)
        tf.addRow("--training.batch_size:", self._batch_size)

        self._lr = QLineEdit("1e-5")
        tf.addRow("--training.lr:", self._lr)

        self._eval_freq = QSpinBox()
        self._eval_freq.setRange(100, 100_000)
        self._eval_freq.setValue(10_000)
        tf.addRow("--training.eval_freq:", self._eval_freq)

        self._save_freq = QSpinBox()
        self._save_freq.setRange(100, 100_000)
        self._save_freq.setValue(10_000)
        tf.addRow("--training.save_freq:", self._save_freq)

        self._log_freq = QSpinBox()
        self._log_freq.setRange(1, 1000)
        self._log_freq.setValue(100)
        tf.addRow("--training.log_freq:", self._log_freq)

        train_group.setLayout(tf)
        cl.addWidget(train_group)

        # ---- Advanced ----
        adv_group = QGroupBox("Advanced Options")
        adv_group.setCheckable(True)
        adv_group.setChecked(False)
        af = QFormLayout()

        self._wandb = QCheckBox()
        af.addRow("--wandb.enable:", self._wandb)

        self._wandb_project = QLineEdit()
        self._wandb_project.setPlaceholderText("my_project")
        af.addRow("--wandb.project:", self._wandb_project)

        self._resume_training = QCheckBox()
        af.addRow("--resume:", self._resume_training)

        self._seed = QSpinBox()
        self._seed.setRange(0, 999999)
        self._seed.setValue(1)
        af.addRow("--seed:", self._seed)

        self._extra_args = QLineEdit()
        self._extra_args.setPlaceholderText("Additional CLI arguments")
        af.addRow("Extra args:", self._extra_args)

        adv_group.setLayout(af)
        cl.addWidget(adv_group)
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ---- Controls ----
        ctrl = QHBoxLayout()
        self._start_btn = QPushButton("Start Training")
        self._start_btn.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #1a73e8; color: white;"
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

        # Output
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(250)
        self._output.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self._output)

    def _build_command(self) -> list[str]:
        cmd = ["lerobot-train"]
        cmd += ["--policy.type", self._policy.currentText()]
        if self._dataset_repo.text().strip():
            cmd += ["--dataset.repo_id", self._dataset_repo.text().strip()]
        if self._output_dir.text().strip():
            cmd += ["--output_dir", self._output_dir.text().strip()]
        cmd += ["--device", self._device.currentText()]
        cmd += ["--training.num_steps", str(self._steps.value())]
        cmd += ["--training.batch_size", str(self._batch_size.value())]
        if self._lr.text().strip():
            cmd += ["--training.lr", self._lr.text().strip()]
        cmd += ["--training.eval_freq", str(self._eval_freq.value())]
        cmd += ["--training.save_freq", str(self._save_freq.value())]
        cmd += ["--training.log_freq", str(self._log_freq.value())]
        if self._wandb.isChecked():
            cmd += ["--wandb.enable", "true"]
            if self._wandb_project.text().strip():
                cmd += ["--wandb.project", self._wandb_project.text().strip()]
        if self._resume_training.isChecked():
            cmd += ["--resume", "true"]
        cmd += ["--seed", str(self._seed.value())]
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
            self._proc_mgr.start_process("train", cmd, config_snapshot={
                "policy": self._policy.currentText(),
                "dataset": self._dataset_repo.text(),
                "steps": self._steps.value(),
                "batch_size": self._batch_size.value(),
                "device": self._device.currentText(),
            })
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        logger.info(f"Training started: {cmd_str}")

    def _on_stop(self):
        if self._proc_mgr:
            self._proc_mgr.kill_process("train")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_output(self, tid, line):
        if tid == "train":
            self._output.appendPlainText(line)

    def _on_highlight(self, tid, line):
        if tid == "train":
            self._output.appendPlainText(f">>> {line}")

    def _on_finished(self, tid, code):
        if tid == "train":
            self._output.appendPlainText(f"\n--- Training finished (exit: {code}) ---")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

    def _copy_cmd(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(" ".join(self._build_command()))
