"""Safety filter for robot actions — enforces limits before sending commands."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class SafetyFilter:
    """
    Filters actions before they reach the robot.

    Enforces:
    - Joint position clamping (hard limits)
    - Velocity limiting (max change per step)
    - Dead zone (ignore tiny movements)
    - Timeout auto-stop (no input -> hold position)
    """

    def __init__(
        self,
        joint_limits: dict[str, tuple[float, float]] | None = None,
        max_velocity: float = 0.5,
        deadzone: float = 0.001,
        timeout_ms: float = 500,
    ):
        self.joint_limits = joint_limits or {}
        self.max_velocity = max_velocity
        self.deadzone = deadzone
        self.timeout_ms = timeout_ms
        self._last_action: dict[str, float] = {}
        self._last_input_time: float = time.time()
        self._enabled = True
        self._e_stopped = False

    @property
    def is_e_stopped(self) -> bool:
        return self._e_stopped

    def set_e_stop(self, active: bool) -> None:
        self._e_stopped = active
        if active:
            logger.warning("SafetyFilter: E-STOP activated")
        else:
            logger.info("SafetyFilter: E-STOP released")

    def filter_action(self, action: dict[str, float]) -> dict[str, float] | None:
        """Filter an action. Returns None if action should be blocked (E-STOP)."""
        if self._e_stopped:
            return None

        if not self._enabled:
            return action

        self._last_input_time = time.time()
        filtered: dict[str, float] = {}

        for key, value in action.items():
            joint_name = key.replace(".pos", "")

            # 1. Clamp to joint limits
            if joint_name in self.joint_limits:
                lo, hi = self.joint_limits[joint_name]
                value = max(lo, min(hi, value))

            # 2. Velocity limit
            if key in self._last_action:
                delta = value - self._last_action[key]
                if abs(delta) > self.max_velocity:
                    value = self._last_action[key] + self.max_velocity * (
                        1 if delta > 0 else -1
                    )

            # 3. Dead zone
            if (
                key in self._last_action
                and abs(value - self._last_action[key]) < self.deadzone
            ):
                value = self._last_action[key]

            filtered[key] = value

        self._last_action = filtered
        return filtered

    def check_timeout(self) -> bool:
        """Return True if input has timed out (should auto-stop)."""
        return (time.time() - self._last_input_time) * 1000 > self.timeout_ms

    def reset(self) -> None:
        self._last_action = {}
        self._last_input_time = time.time()
        self._e_stopped = False
