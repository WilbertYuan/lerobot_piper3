"""Cameras page — camera selection, dynamic params, live preview, FPS stats."""

from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.adapters.cameras.base_adapter import BaseCameraAdapter
from lerobot_gui.adapters.cameras.opencv_adapter import OpenCVCameraAdapter
from lerobot_gui.adapters.cameras.realsense_adapter import RealSenseCameraAdapter
from lerobot_gui.adapters.registry import AdapterRegistry
from lerobot_gui.schemas import SchemaLoader
from lerobot_gui.services.task_manager import TaskManager
from lerobot_gui.widgets.dynamic_form import DynamicFormWidget
from lerobot_gui.widgets.video_widget import VideoWidget

logger = logging.getLogger(__name__)

_CAMERA_ADAPTER_MAP: dict[str, type] = {
    "opencv": OpenCVCameraAdapter,
    "intelrealsense": RealSenseCameraAdapter,
}


class CamerasPage(QWidget):
    def __init__(
        self,
        schema_loader: SchemaLoader | None = None,
        adapter_registry: AdapterRegistry | None = None,
        task_manager: TaskManager | None = None,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self._schemas = schema_loader
        self._registry = adapter_registry
        self._tasks = task_manager
        self._adapter: BaseCameraAdapter | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top bar
        top = QHBoxLayout()
        top.addWidget(QLabel("Camera Type:"))
        self._type_combo = QComboBox()
        if self._schemas:
            for s in self._schemas.list_schemas("camera"):
                self._type_combo.addItem(f"{s.display_name} ({s.device_type})", s.device_type)
        else:
            self._type_combo.addItem("OpenCV Camera (opencv)", "opencv")
            self._type_combo.addItem("Intel RealSense (intelrealsense)", "intelrealsense")
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        top.addWidget(self._type_combo, 1)
        layout.addLayout(top)

        # Splitter: left (form + controls) | right (video)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        left = QWidget()
        ll = QVBoxLayout(left)

        self._form = DynamicFormWidget()
        ll.addWidget(self._form, 1)

        ctrl = QGroupBox("Controls")
        cl = QVBoxLayout()
        self._open_btn = QPushButton("Open Camera")
        self._open_btn.setStyleSheet(
            "font-size: 14px; padding: 8px; background-color: #228B22; color: white;"
        )
        self._open_btn.clicked.connect(self._on_open)
        cl.addWidget(self._open_btn)

        self._close_btn = QPushButton("Close Camera")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._on_close)
        cl.addWidget(self._close_btn)

        self._screenshot_btn = QPushButton("Screenshot")
        self._screenshot_btn.setEnabled(False)
        self._screenshot_btn.clicked.connect(self._on_screenshot)
        cl.addWidget(self._screenshot_btn)

        self._status = QLabel("Status: Closed")
        cl.addWidget(self._status)

        self._fps_label = QLabel("FPS: —")
        self._fps_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        cl.addWidget(self._fps_label)
        ctrl.setLayout(cl)
        ll.addWidget(ctrl)
        splitter.addWidget(left)

        # Right panel: video
        right = QWidget()
        rl = QVBoxLayout(right)
        self._video = VideoWidget()
        rl.addWidget(self._video, 1)
        splitter.addWidget(right)
        splitter.setSizes([350, 600])
        layout.addWidget(splitter)

        # Timer for frame polling
        self._frame_timer = QTimer()
        self._frame_timer.timeout.connect(self._poll_frame)

        if self._type_combo.count() > 0:
            self._on_type_changed(0)

    def _on_type_changed(self, _index: int):
        dtype = self._type_combo.currentData()
        if self._schemas:
            schema = self._schemas.get(dtype)
            self._form.set_schema(schema)

    def _on_open(self):
        dtype = self._type_combo.currentData()
        params = self._form.get_values()

        adapter_cls = _CAMERA_ADAPTER_MAP.get(dtype)
        if adapter_cls is None:
            logger.warning(f"No adapter for camera type: {dtype}")
            self._status.setText(f"No adapter for {dtype}")
            return

        self._adapter = adapter_cls()
        self._open_btn.setEnabled(False)
        self._status.setText("Opening...")

        def do_open():
            self._adapter.open(params)

        if self._tasks:
            task = self._tasks.submit("camera_open", do_open)
            task.signals.finished.connect(self._on_opened)
            task.signals.error.connect(self._on_open_error)
        else:
            try:
                do_open()
                self._on_opened("", None)
            except Exception as e:
                self._on_open_error("", str(e))

    def _on_opened(self, _tid, _result):
        self._status.setText("Status: Open")
        self._status.setStyleSheet("color: #44ff44;")
        self._open_btn.setEnabled(False)
        self._close_btn.setEnabled(True)
        self._screenshot_btn.setEnabled(True)
        self._frame_timer.start(33)  # ~30fps polling
        logger.info("Camera opened")

    def _on_open_error(self, _tid, tb):
        self._status.setText("Open failed!")
        self._status.setStyleSheet("color: #ff4444;")
        self._open_btn.setEnabled(True)
        logger.error(f"Camera open error:\n{tb}")

    def _on_close(self):
        self._frame_timer.stop()
        if self._adapter:
            self._adapter.close()
        self._adapter = None
        self._status.setText("Status: Closed")
        self._status.setStyleSheet("color: #cccccc;")
        self._open_btn.setEnabled(True)
        self._close_btn.setEnabled(False)
        self._screenshot_btn.setEnabled(False)
        self._video.setText("No video feed")
        self._fps_label.setText("FPS: —")

    def _poll_frame(self):
        if not self._adapter or not self._adapter.is_open:
            return
        frame = self._adapter.read_frame()
        if frame is not None:
            self._video.update_frame(frame)
        stats = self._adapter.fps_stats()
        self._fps_label.setText(f"FPS: {stats.get('measured_fps', 0):.1f}")

    def _on_screenshot(self):
        if not self._adapter or not self._adapter.is_open:
            return
        frame = self._adapter.read_frame()
        if frame is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "screenshot.png", "Images (*.png *.jpg)"
        )
        if path:
            try:
                from PIL import Image
                img = Image.fromarray(frame)
                img.save(path)
                logger.info(f"Screenshot saved: {path}")
            except ImportError:
                import cv2
                bgr = frame[:, :, ::-1] if frame.shape[2] == 3 else frame
                cv2.imwrite(path, bgr)
                logger.info(f"Screenshot saved: {path}")
