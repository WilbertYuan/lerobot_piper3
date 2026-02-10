"""Specialized adapter for AgileX Piper robot with enhanced safety."""

from __future__ import annotations

import logging
import threading
from typing import Any

from .base_adapter import BaseRobotAdapter

logger = logging.getLogger(__name__)

PIPER_JOINT_LIMITS = {
    "joint_1": (-1.605, 1.605),
    "joint_2": (-0.042, 2.093),
    "joint_3": (-1.919, 0.052),
    "joint_4": (-1.570, 1.570),
    "joint_5": (-1.396, 1.396),
    "joint_6": (-1.570, 1.570),
    "gripper": (0.0, 0.08),
}
MOTOR_ORDER = ["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6", "gripper"]


class PiperRobotAdapter(BaseRobotAdapter):
    """
    Piper follower adapter with:
    - Direct CAN bus access for fast emergency stop
    - Known joint limits for SafetyFilter
    - Piper-specific diagnostics
    """

    def __init__(self):
        self._robot = None
        self._lock = threading.Lock()

    def connect(self, params: dict[str, Any]) -> None:
        with self._lock:
            from lerobot.robots.piper_follower.config_piper_follower import PiperFollowerConfig
            from lerobot.motors.piper.piper import PiperMotorsBusConfig

            can_name = params.get("can_name", "can_slave1")
            robot_id = params.get("id") or None
            motors = params.get("motors", {
                "joint_1": (1, "agilex_piper"), "joint_2": (2, "agilex_piper"),
                "joint_3": (3, "agilex_piper"), "joint_4": (4, "agilex_piper"),
                "joint_5": (5, "agilex_piper"), "joint_6": (6, "agilex_piper"),
                "gripper": (7, "agilex_piper"),
            })
            # Ensure motors values are tuples
            motors = {k: tuple(v) if isinstance(v, list) else v for k, v in motors.items()}

            motor_cfg = PiperMotorsBusConfig(can_name=can_name, motors=motors)
            cameras = self._build_cameras(params.get("cameras", {}))
            config = PiperFollowerConfig(id=robot_id, motors=motor_cfg, cameras=cameras)

            from lerobot.robots.piper_follower.piper_follower import PiperFollower
            self._robot = PiperFollower(config)
            self._robot.connect()
            logger.info(f"PiperAdapter: connected (CAN={can_name})")

    def _build_cameras(self, cam_params: dict) -> dict:
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
                    logger.error(f"Piper disconnect error: {e}")
                finally:
                    self._robot = None

    @property
    def is_connected(self) -> bool:
        return self._robot is not None and self._robot.is_connected

    def get_state(self) -> dict[str, float]:
        with self._lock:
            if not self._robot:
                return {}
            state = self._robot.bus.read()
            return {f"{k}.pos": float(v) for k, v in state.items()}

    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        with self._lock:
            if not self._robot:
                return action
            return self._robot.send_action(action)

    def stop(self) -> None:
        if self.is_connected:
            state = self.get_state()
            if state:
                self.send_action(state)

    def emergency_stop(self) -> None:
        with self._lock:
            if self._robot and self._robot.bus:
                try:
                    self._robot.bus.piper.DisableArm(7)
                    self._robot.bus.piper.GripperCtrl(0, 1000, 0x02, 0)
                    logger.warning("PIPER E-STOP: arm disabled")
                except Exception as e:
                    logger.error(f"E-STOP error: {e}")
                self._robot = None

    def get_diagnostics(self) -> dict[str, Any]:
        if not self._robot:
            return {"status": "disconnected"}
        try:
            info = self._robot.bus.piper.GetArmLowSpdInfoMsgs()
            enable_status = [
                getattr(getattr(info, f"motor_{i}").foc_status, "driver_enable_status", False)
                for i in range(1, 7)
            ]
            return {
                "status": "connected",
                "robot_type": "piper_follower",
                "motors_enabled": enable_status,
                "is_calibrated": self._robot.is_calibrated,
                "joint_limits": PIPER_JOINT_LIMITS,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_action_names(self) -> list[str]:
        return [f"{m}.pos" for m in MOTOR_ORDER]

    def get_state_names(self) -> list[str]:
        return [f"{m}.pos" for m in MOTOR_ORDER]
