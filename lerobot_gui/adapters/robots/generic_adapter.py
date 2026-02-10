"""
Generic robot adapter — wraps ANY LeRobot Robot via make_robot_from_config.

Handles SO100, Koch, Omx, BiSO, HopeJr, OpenArm, Reachy2, Unitree G1,
LeKiwi, EarthRover, and any future registered robot type.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
from typing import Any

from .base_adapter import BaseRobotAdapter

logger = logging.getLogger(__name__)


class GenericRobotAdapter(BaseRobotAdapter):

    def __init__(self):
        self._robot = None
        self._robot_type: str = ""
        self._lock = threading.Lock()

    def connect(self, params: dict[str, Any]) -> None:
        with self._lock:
            params = dict(params)
            robot_type = params.pop("_robot_type", "")
            self._robot_type = robot_type
            config = self._build_config(robot_type, params)

            from lerobot.robots.utils import make_robot_from_config
            self._robot = make_robot_from_config(config)
            self._robot.connect()
            logger.info(f"GenericAdapter: connected {robot_type}")

    def _build_config(self, robot_type: str, params: dict[str, Any]) -> Any:
        from lerobot.robots.config import RobotConfig
        config_cls = RobotConfig.get_choice_class(robot_type)
        if config_cls is None:
            raise ValueError(f"Unknown robot type: {robot_type}")

        cameras = self._build_cameras(params.pop("cameras", {}))

        # Flatten nested dotted keys (e.g. "left_arm_config.port")
        nested: dict[str, dict[str, Any]] = {}
        flat: dict[str, Any] = {}
        for k, v in params.items():
            if "." in k:
                parts = k.split(".", 1)
                nested.setdefault(parts[0], {})[parts[1]] = v
            else:
                flat[k] = v

        # Filter to valid fields
        valid_fields = {f.name for f in dataclasses.fields(config_cls)}
        filtered = {k: v for k, v in flat.items() if k in valid_fields and v is not None and v != ""}

        # Handle nested configs (bimanual arms, etc.)
        for nest_key, nest_vals in nested.items():
            if nest_key in valid_fields:
                filtered[nest_key] = nest_vals

        if cameras:
            filtered["cameras"] = cameras

        return config_cls(**filtered)

    def _build_cameras(self, cam_params: Any) -> dict:
        if not cam_params or not isinstance(cam_params, dict):
            return {}
        from lerobot.cameras.configs import CameraConfig
        cameras = {}
        for name, cfg in cam_params.items():
            if not isinstance(cfg, dict):
                continue
            cfg = dict(cfg)
            cam_type = cfg.pop("type", "opencv")
            cam_cls = CameraConfig.get_choice_class(cam_type)
            if cam_cls:
                cameras[name] = cam_cls(**cfg)
        return cameras

    def disconnect(self) -> None:
        with self._lock:
            if self._robot:
                try:
                    self._robot.disconnect()
                except Exception as e:
                    logger.error(f"Disconnect error: {e}")
                finally:
                    self._robot = None

    @property
    def is_connected(self) -> bool:
        return self._robot is not None and self._robot.is_connected

    def get_state(self) -> dict[str, float]:
        with self._lock:
            if self._robot is None:
                return {}
            obs = self._robot.get_observation()
            return {k: float(v) for k, v in obs.items() if isinstance(v, (int, float))}

    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        with self._lock:
            if self._robot is None:
                return action
            return self._robot.send_action(action)

    def stop(self) -> None:
        if self.is_connected:
            state = self.get_state()
            if state:
                self.send_action(state)

    def emergency_stop(self) -> None:
        with self._lock:
            if self._robot is None:
                return
            try:
                self._robot.disconnect()
            except Exception as e:
                logger.error(f"Emergency stop error: {e}")
            finally:
                self._robot = None

    def get_diagnostics(self) -> dict[str, Any]:
        if self._robot is None:
            return {"status": "disconnected"}
        return {
            "status": "connected",
            "robot_type": self._robot_type,
            "is_calibrated": getattr(self._robot, "is_calibrated", None),
        }

    def get_action_names(self) -> list[str]:
        if self._robot is None:
            return []
        try:
            return list(self._robot.action_features.keys())
        except Exception:
            return []

    def get_state_names(self) -> list[str]:
        if self._robot is None:
            return []
        try:
            feat = self._robot.observation_features
            return [k for k, v in feat.items() if not isinstance(v, tuple)]
        except Exception:
            return []
