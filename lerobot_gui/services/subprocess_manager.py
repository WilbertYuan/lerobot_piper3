"""Subprocess manager for training/inference — streams output to GUI."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class SubprocessManager(QObject):
    """
    Manages long-running subprocesses (training, eval, etc.).
    Streams stdout/stderr to GUI in real time.
    """

    output_line = Signal(str, str)       # task_id, line
    highlight_line = Signal(str, str)    # task_id, line (loss/step/error)
    process_finished = Signal(str, int)  # task_id, return_code
    process_started = Signal(str, str)   # task_id, command_str

    def __init__(self, runs_dir: Path | None = None):
        super().__init__()
        self.runs_dir = runs_dir or Path("runs")
        self._processes: dict[str, subprocess.Popen] = {}
        self._threads: dict[str, threading.Thread] = {}

    def start_process(
        self,
        task_id: str,
        command: list[str],
        env: dict[str, str] | None = None,
        config_snapshot: dict[str, Any] | None = None,
    ) -> None:
        """Start a subprocess and stream its output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.runs_dir / f"{task_id}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        if config_snapshot:
            with open(run_dir / "config_snapshot.json", "w") as f:
                json.dump(config_snapshot, f, indent=2, default=str)

        cmd_str = " ".join(command)
        (run_dir / "command.txt").write_text(cmd_str)

        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)

        self.process_started.emit(task_id, cmd_str)
        logger.info(f"Starting subprocess: {cmd_str}")

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=proc_env,
        )
        self._processes[task_id] = proc

        log_path = run_dir / "run.log"
        t = threading.Thread(
            target=self._stream_output, args=(task_id, proc, log_path), daemon=True
        )
        self._threads[task_id] = t
        t.start()

    def _stream_output(
        self, task_id: str, proc: subprocess.Popen, log_path: Path
    ) -> None:
        highlight_patterns = [
            re.compile(r"loss[:\s]", re.IGNORECASE),
            re.compile(r"step[:\s]", re.IGNORECASE),
            re.compile(r"error", re.IGNORECASE),
            re.compile(r"exception", re.IGNORECASE),
            re.compile(r"epoch[:\s]", re.IGNORECASE),
        ]
        with open(log_path, "w") as log_file:
            for line in proc.stdout:
                line = line.rstrip("\n")
                log_file.write(line + "\n")
                log_file.flush()
                self.output_line.emit(task_id, line)
                for pat in highlight_patterns:
                    if pat.search(line):
                        self.highlight_line.emit(task_id, line)
                        break

        proc.wait()
        self.process_finished.emit(task_id, proc.returncode)
        logger.info(f"Subprocess {task_id} finished with code {proc.returncode}")

    def kill_process(self, task_id: str) -> None:
        if task_id in self._processes:
            self._processes[task_id].kill()
            logger.warning(f"Killed subprocess: {task_id}")

    def get_command_str(self, task_id: str) -> str | None:
        proc = self._processes.get(task_id)
        if proc and proc.args:
            return " ".join(proc.args) if isinstance(proc.args, list) else str(proc.args)
        return None
