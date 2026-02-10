"""Central adapter registry — maps device type names to adapter classes."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Singleton registry mapping device type strings to adapter classes.

    Usage:
        registry = AdapterRegistry()
        registry.register_robot("piper_follower", PiperRobotAdapter)
        adapter_cls = registry.get_robot_adapter("piper_follower")
    """

    _instance: AdapterRegistry | None = None

    def __new__(cls) -> AdapterRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._robots = {}
            cls._instance._cameras = {}
            cls._instance._teleops = {}
        return cls._instance

    # ---- Robot adapters ----

    def register_robot(self, type_name: str, adapter_cls: type) -> None:
        self._robots[type_name] = adapter_cls
        logger.debug(f"Registered robot adapter: {type_name}")

    def get_robot_adapter(self, type_name: str) -> type | None:
        return self._robots.get(type_name)

    def list_robot_types(self) -> list[str]:
        return list(self._robots.keys())

    # ---- Camera adapters ----

    def register_camera(self, type_name: str, adapter_cls: type) -> None:
        self._cameras[type_name] = adapter_cls

    def get_camera_adapter(self, type_name: str) -> type | None:
        return self._cameras.get(type_name)

    def list_camera_types(self) -> list[str]:
        return list(self._cameras.keys())

    # ---- Teleoperator adapters ----

    def register_teleop(self, type_name: str, adapter_cls: type) -> None:
        self._teleops[type_name] = adapter_cls

    def get_teleop_adapter(self, type_name: str) -> type | None:
        return self._teleops.get(type_name)

    def list_teleop_types(self) -> list[str]:
        return list(self._teleops.keys())
