"""Main window — navigation sidebar + stacked pages + E-STOP bar."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.adapters.registry import AdapterRegistry
from lerobot_gui.adapters.robots.generic_adapter import GenericRobotAdapter
from lerobot_gui.adapters.robots.piper_adapter import PiperRobotAdapter
from lerobot_gui.pages.cameras_page import CamerasPage
from lerobot_gui.pages.dataset_page import DatasetPage
from lerobot_gui.pages.devices_page import DevicesPage
from lerobot_gui.pages.home_page import HomePage
from lerobot_gui.pages.infer_page import InferPage
from lerobot_gui.pages.logs_page import LogsPage
from lerobot_gui.pages.record_page import RecordPage
from lerobot_gui.pages.settings_page import SettingsPage
from lerobot_gui.pages.teleop_page import TeleopPage
from lerobot_gui.pages.train_page import TrainPage
from lerobot_gui.schemas import SchemaLoader
from lerobot_gui.services.config_store import ConfigStore
from lerobot_gui.services.logger_bridge import setup_gui_logging
from lerobot_gui.services.safety_filter import SafetyFilter
from lerobot_gui.services.subprocess_manager import SubprocessManager
from lerobot_gui.services.task_manager import TaskManager
from lerobot_gui.widgets.estop_button import EStopButton

logger = logging.getLogger(__name__)

NAV_ITEMS = [
    ("Home", "Project & Environment"),
    ("Devices", "Robot Connection"),
    ("Cameras", "Camera Preview"),
    ("Teleop", "Manual Control"),
    ("Record", "Data Collection"),
    ("Dataset", "Browse & Replay"),
    ("Train", "Policy Training"),
    ("Infer", "Deploy & Evaluate"),
    ("Logs", "Log Viewer"),
    ("Settings", "Preferences"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual-Lerobot — Robot Workstation")
        self.setMinimumSize(1200, 800)

        # ---- Initialize services ----
        self._config_store = ConfigStore()
        self._task_manager = TaskManager()
        self._subprocess_mgr = SubprocessManager()
        self._safety_filter = SafetyFilter()

        # ---- Schema system ----
        self._schema_loader = SchemaLoader()
        self._schema_loader.load_all()

        # ---- Adapter registry ----
        self._adapter_registry = AdapterRegistry()
        self._adapter_registry.register_robot("piper_follower", PiperRobotAdapter)
        for rtype in self._schema_loader.list_types("robot"):
            if rtype not in self._adapter_registry.list_robot_types():
                self._adapter_registry.register_robot(rtype, GenericRobotAdapter)

        # ---- Logging (must be before pages that log) ----
        self._log_handler = setup_gui_logging()

        # ---- Build UI ----
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content = QHBoxLayout()
        content.setSpacing(0)

        # Sidebar navigation
        self._nav = QListWidget()
        self._nav.setFixedWidth(180)
        self._nav.setStyleSheet(
            "QListWidget {"
            "  font-size: 14px;"
            "  background-color: #2b2b2b;"
            "  color: #ddd;"
            "  border: none;"
            "  outline: none;"
            "}"
            "QListWidget::item {"
            "  padding: 14px 12px;"
            "  border-bottom: 1px solid #3a3a3a;"
            "}"
            "QListWidget::item:selected {"
            "  background-color: #1a73e8;"
            "  color: white;"
            "}"
            "QListWidget::item:hover:!selected {"
            "  background-color: #353535;"
            "}"
        )
        for name, tooltip in NAV_ITEMS:
            item = QListWidgetItem(name)
            item.setToolTip(tooltip)
            self._nav.addItem(item)
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        content.addWidget(self._nav)

        # Page stack
        self._stack = QStackedWidget()

        # Create pages
        self._home = HomePage(self._config_store)
        self._devices = DevicesPage(
            self._schema_loader, self._adapter_registry,
            self._task_manager, self._config_store,
        )
        self._cameras = CamerasPage(
            self._schema_loader, self._adapter_registry, self._task_manager,
        )
        self._teleop = TeleopPage(self._schema_loader, self._safety_filter)
        self._record = RecordPage(self._subprocess_mgr)
        self._dataset = DatasetPage(self._subprocess_mgr)
        self._train = TrainPage(self._subprocess_mgr)
        self._infer = InferPage(self._subprocess_mgr)
        self._logs = LogsPage()
        self._settings = SettingsPage(self._config_store)

        for page in [
            self._home,
            self._devices,
            self._cameras,
            self._teleop,
            self._record,
            self._dataset,
            self._train,
            self._infer,
            self._logs,
            self._settings,
        ]:
            self._stack.addWidget(page)

        content.addWidget(self._stack, 1)
        main_layout.addLayout(content, 1)

        # E-STOP bar at bottom
        self._estop = EStopButton()
        self._estop.e_stop_triggered.connect(self._on_estop)
        self._estop.e_stop_released.connect(self._on_estop_release)
        main_layout.addWidget(self._estop)

        # Connect logging to Logs page
        self._log_handler.emitter.log_record.connect(
            self._logs.log_viewer.append_log
        )

        # Select Home page
        self._nav.setCurrentRow(0)

        logger.info("Visual-Lerobot GUI initialized")

    def _on_nav_changed(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    def _on_estop(self):
        logger.warning("E-STOP TRIGGERED")
        self._safety_filter.set_e_stop(True)
        # Try to emergency-stop connected robot
        adapter = self._devices.get_current_adapter()
        if adapter is not None and hasattr(adapter, "is_connected") and adapter.is_connected:
            try:
                adapter.emergency_stop()
            except Exception as e:
                logger.error(f"E-STOP adapter error: {e}")

    def _on_estop_release(self):
        logger.info("E-STOP released")
        self._safety_filter.set_e_stop(False)
