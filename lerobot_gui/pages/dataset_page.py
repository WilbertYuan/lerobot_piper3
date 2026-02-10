"""Dataset page — browse episodes, show stats, replay via CLI."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from lerobot_gui.services.subprocess_manager import SubprocessManager

logger = logging.getLogger(__name__)


class DatasetPage(QWidget):
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

        # Dataset selection
        top = QGroupBox("Dataset")
        tl = QHBoxLayout()
        self._repo_id = QLineEdit()
        self._repo_id.setPlaceholderText("user/dataset_name or local path")
        tl.addWidget(QLabel("Repo ID / Path:"))
        tl.addWidget(self._repo_id, 1)
        btn_browse = QPushButton("Browse Local...")
        btn_browse.clicked.connect(self._browse_local)
        tl.addWidget(btn_browse)
        btn_load = QPushButton("Load Info")
        btn_load.clicked.connect(self._load_dataset_info)
        tl.addWidget(btn_load)
        top.setLayout(tl)
        layout.addWidget(top)

        # Splitter: info | replay control
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: dataset info + episode list
        left = QWidget()
        ll = QVBoxLayout(left)

        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setMaximumHeight(200)
        ll.addWidget(QLabel("Dataset Info:"))
        ll.addWidget(self._info_text)

        ll.addWidget(QLabel("Episodes:"))
        self._episode_list = QListWidget()
        ll.addWidget(self._episode_list)

        splitter.addWidget(left)

        # Right: replay controls + output
        right = QWidget()
        rl = QVBoxLayout(right)

        replay_group = QGroupBox("Replay / Visualize")
        rf = QFormLayout()

        self._replay_robot = QComboBox()
        self._replay_robot.setEditable(True)
        self._replay_robot.addItems([
            "piper_follower", "so100_follower", "koch_follower",
        ])
        rf.addRow("Robot Type:", self._replay_robot)

        self._replay_episode = QSpinBox()
        self._replay_episode.setRange(0, 99999)
        rf.addRow("Episode:", self._replay_episode)

        self._replay_fps = QSpinBox()
        self._replay_fps.setRange(1, 120)
        self._replay_fps.setValue(30)
        rf.addRow("FPS:", self._replay_fps)

        replay_group.setLayout(rf)
        rl.addWidget(replay_group)

        btn_row = QHBoxLayout()
        self._replay_btn = QPushButton("Replay on Robot")
        self._replay_btn.setStyleSheet(
            "font-size: 14px; padding: 8px; background-color: #1a73e8; color: white;"
        )
        self._replay_btn.clicked.connect(self._on_replay)
        btn_row.addWidget(self._replay_btn)

        self._viz_btn = QPushButton("Visualize Dataset")
        self._viz_btn.clicked.connect(self._on_visualize)
        btn_row.addWidget(self._viz_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        btn_row.addWidget(self._stop_btn)
        rl.addLayout(btn_row)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setStyleSheet("font-family: monospace; font-size: 11px;")
        rl.addWidget(self._output)

        splitter.addWidget(right)
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)

    def _browse_local(self):
        path = QFileDialog.getExistingDirectory(self, "Select Dataset Directory")
        if path:
            self._repo_id.setText(path)

    def _load_dataset_info(self):
        repo_id = self._repo_id.text().strip()
        if not repo_id:
            return
        try:
            from lerobot.datasets.lerobot_dataset import LeRobotDataset
            ds = LeRobotDataset(repo_id)
            info_lines = [
                f"Repo: {repo_id}",
                f"Total frames: {len(ds)}",
                f"Episodes: {ds.meta.total_episodes}",
                f"FPS: {ds.fps}",
                f"Features: {list(ds.meta.features.keys()) if hasattr(ds.meta, 'features') else 'N/A'}",
            ]
            self._info_text.setPlainText("\n".join(info_lines))
            self._episode_list.clear()
            for i in range(ds.meta.total_episodes):
                self._episode_list.addItem(f"Episode {i}")
            logger.info(f"Dataset loaded: {repo_id} ({ds.meta.total_episodes} episodes)")
        except Exception as e:
            self._info_text.setPlainText(f"Error loading dataset:\n{e}")
            logger.error(f"Dataset load error: {e}")

    def _on_replay(self):
        cmd = [
            "lerobot-replay",
            "--robot.type", self._replay_robot.currentText(),
            "--dataset.repo_id", self._repo_id.text().strip(),
            "--episode", str(self._replay_episode.value()),
            "--fps", str(self._replay_fps.value()),
        ]
        self._run_subprocess("replay", cmd)

    def _on_visualize(self):
        cmd = [
            "python", "-m", "lerobot.scripts.visualize_dataset",
            "--dataset.repo_id", self._repo_id.text().strip(),
        ]
        self._run_subprocess("viz", cmd)

    def _run_subprocess(self, task_id: str, cmd: list[str]):
        self._output.clear()
        self._output.appendPlainText(f"$ {' '.join(cmd)}\n")
        if self._proc_mgr:
            self._proc_mgr.output_line.connect(self._on_output)
            self._proc_mgr.process_finished.connect(self._on_finished)
            self._proc_mgr.start_process(task_id, cmd)
        self._stop_btn.setEnabled(True)

    def _on_stop(self):
        if self._proc_mgr:
            self._proc_mgr.kill_process("replay")
            self._proc_mgr.kill_process("viz")
        self._stop_btn.setEnabled(False)

    def _on_output(self, task_id: str, line: str):
        self._output.appendPlainText(line)

    def _on_finished(self, task_id: str, code: int):
        self._output.appendPlainText(f"\n--- {task_id} finished (exit code: {code}) ---")
        self._stop_btn.setEnabled(False)
