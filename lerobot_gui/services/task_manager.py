"""Background task management — keeps GUI responsive."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

logger = logging.getLogger(__name__)


class TaskSignals(QObject):
    """Signals emitted by background tasks."""

    started = Signal(str)
    progress = Signal(str, int)
    finished = Signal(str, object)
    error = Signal(str, str)
    cancelled = Signal(str)


class Task(QRunnable):
    """A background task that runs a callable in QThreadPool."""

    def __init__(self, task_id: str, fn: Callable, *args: Any, **kwargs: Any):
        super().__init__()
        self.task_id = task_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()
        self._cancelled = False
        self.setAutoDelete(True)

    def cancel(self):
        self._cancelled = True

    @Slot()
    def run(self):
        self.signals.started.emit(self.task_id)
        try:
            result = self.fn(*self.args, **self.kwargs)
            if not self._cancelled:
                self.signals.finished.emit(self.task_id, result)
            else:
                self.signals.cancelled.emit(self.task_id)
        except Exception:
            tb = traceback.format_exc()
            logger.error(f"Task {self.task_id} failed:\n{tb}")
            self.signals.error.emit(self.task_id, tb)


class TaskManager(QObject):
    """Manages background tasks for all robot/camera operations."""

    task_started = Signal(str)
    task_finished = Signal(str, object)
    task_error = Signal(str, str)
    task_cancelled = Signal(str)

    def __init__(self, max_threads: int = 8):
        super().__init__()
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(max_threads)
        self._tasks: dict[str, Task] = {}

    def submit(self, task_id: str, fn: Callable, *args: Any, **kwargs: Any) -> Task:
        task = Task(task_id, fn, *args, **kwargs)
        task.signals.started.connect(self.task_started)
        task.signals.finished.connect(self.task_finished)
        task.signals.error.connect(self.task_error)
        task.signals.cancelled.connect(self.task_cancelled)
        self._tasks[task_id] = task
        self._pool.start(task)
        logger.debug(f"Task submitted: {task_id}")
        return task

    def cancel(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].cancel()

    def is_running(self, task_id: str) -> bool:
        return task_id in self._tasks and not self._tasks[task_id]._cancelled
