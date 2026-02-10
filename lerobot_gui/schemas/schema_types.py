"""
Schema type definitions for the dynamic form system.

Defines the data structures that drive automatic UI generation for any
robot, camera, or teleoperator device.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class FieldType(enum.Enum):
    """Supported field types for dynamic form generation."""

    STRING = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    ENUM = "enum"
    PATH = "path"
    LIST_FLOAT = "list_float"
    LIST_INT = "list_int"
    LIST_STR = "list_str"
    DICT = "dict"
    SERIAL_PORT = "serial_port"
    DEVICE_ID = "device_id"
    CAN_INTERFACE = "can_interface"
    IP_ADDRESS = "ip_address"
    MOTOR_MAP = "motor_map"
    MOTOR_MAP_NORM = "motor_map_norm"
    MOTOR_CONFIG_DAMIAO = "motor_config_damiao"
    CAMERA_DICT = "camera_dict"
    JOINT_LIMITS = "joint_limits"
    TELEOP_KEYS = "teleop_keys"
    NESTED_CONFIG = "nested_config"


@dataclass
class FieldSchema:
    """Describes a single configuration field for dynamic form rendering."""

    key: str
    label: str
    type: FieldType
    default: Any = None
    required: bool = False
    help: str = ""
    choices: list[str] | None = None
    min_val: float | None = None
    max_val: float | None = None
    step: float | None = None
    advanced: bool = False
    group: str = "general"
    depends_on: str | None = None
    depends_value: Any = None
    validator: str | None = None
    placeholder: str = ""
    readonly: bool = False
    nested_schema_ref: str | None = None
    list_length: int | None = None
    list_labels: list[str] | None = None


@dataclass
class SchemaGroup:
    """A named group of fields, rendered as a collapsible section."""

    name: str
    label: str
    description: str = ""
    collapsed: bool = False


@dataclass
class DeviceSchema:
    """Complete schema for a device type."""

    version: str
    device_type: str
    device_category: str  # "robot" | "camera" | "teleoperator"
    display_name: str
    description: str = ""
    fields: list[FieldSchema] = field(default_factory=list)
    groups: list[SchemaGroup] = field(
        default_factory=lambda: [
            SchemaGroup("general", "Basic Settings"),
            SchemaGroup("motors", "Motor Configuration"),
            SchemaGroup("cameras", "Camera Configuration"),
            SchemaGroup("network", "Network Settings"),
            SchemaGroup("control", "Control Parameters", collapsed=True),
            SchemaGroup("calibration", "Calibration", collapsed=True),
            SchemaGroup("advanced", "Advanced Settings", collapsed=True),
        ]
    )
    supports_cameras: bool = True
    supports_emergency_stop: bool = True

    def get_fields_by_group(self, group_name: str) -> list[FieldSchema]:
        return [f for f in self.fields if f.group == group_name]

    def get_required_fields(self) -> list[FieldSchema]:
        return [f for f in self.fields if f.required]

    def get_field(self, key: str) -> FieldSchema | None:
        for f in self.fields:
            if f.key == key:
                return f
        return None
