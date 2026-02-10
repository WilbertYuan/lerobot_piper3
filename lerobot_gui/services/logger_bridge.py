"""Bridge Python logging -> Qt signals for real-time log display."""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QObject, Signal


class LogSignalEmitter(QObject):
    """Qt object that emits log records as signals."""

    log_record = Signal(str, str, str)  # level, timestamp, message


class QtLogHandler(logging.Handler):
    """Python logging handler that forwards records to a Qt signal."""

    def __init__(self, emitter: LogSignalEmitter | None = None):
        super().__init__()
        self.emitter = emitter or LogSignalEmitter()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
            self.emitter.log_record.emit(record.levelname, ts, msg)
        except Exception:
            self.handleError(record)


def setup_gui_logging(level: int = logging.DEBUG) -> QtLogHandler:
    """Install a QtLogHandler on the root logger and return it."""
    handler = QtLogHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(name)s: %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)
    return handler
