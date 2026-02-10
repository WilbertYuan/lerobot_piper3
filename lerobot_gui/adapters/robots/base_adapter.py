"""Abstract base class for all robot adapters."""

from __future__ import annotations

import abc
from typing import Any


class BaseRobotAdapter(abc.ABC):
    """
    Stable interface between GUI and any robot hardware.

    GUI code ONLY depends on this interface — never on concrete robot classes.
    """

    @abc.abstractmethod
    def connect(self, params: dict[str, Any]) -> None:
        """Connect to the robot with the given parameters."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Safely disconnect from the robot."""

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool: ...

    @abc.abstractmethod
    def get_state(self) -> dict[str, float]:
        """Return current joint/sensor state as a flat dict."""

    @abc.abstractmethod
    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        """Send an action, return the action actually sent."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Soft stop — hold position."""

    @abc.abstractmethod
    def emergency_stop(self) -> None:
        """Emergency stop — disable motors immediately."""

    @abc.abstractmethod
    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic info."""

    @abc.abstractmethod
    def get_action_names(self) -> list[str]:
        """Ordered list of action dimension names."""

    @abc.abstractmethod
    def get_state_names(self) -> list[str]:
        """Ordered list of state dimension names."""
