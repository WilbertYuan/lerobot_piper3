"""
Schema loader — central registry for all device schemas.

Loads schemas from hand-written overlays that cover every robot,
camera, and teleoperator type in the LeRobot ecosystem.
"""

from __future__ import annotations

import logging

from .schema_types import DeviceSchema

logger = logging.getLogger(__name__)


class SchemaLoader:
    """Central schema registry. Loads and indexes all device schemas."""

    def __init__(self):
        self._schemas: dict[str, DeviceSchema] = {}

    def register(self, schema: DeviceSchema) -> None:
        self._schemas[schema.device_type] = schema

    def get(self, device_type: str) -> DeviceSchema | None:
        return self._schemas.get(device_type)

    def list_types(self, category: str | None = None) -> list[str]:
        if category is None:
            return list(self._schemas.keys())
        return [k for k, v in self._schemas.items() if v.device_category == category]

    def list_schemas(self, category: str | None = None) -> list[DeviceSchema]:
        if category is None:
            return list(self._schemas.values())
        return [v for v in self._schemas.values() if v.device_category == category]

    def load_all(self) -> None:
        """Load all known device schemas."""
        from .robot_schemas import build_all_robot_schemas
        from .camera_schemas import build_all_camera_schemas
        from .teleop_schemas import build_all_teleop_schemas

        for schema in build_all_robot_schemas():
            self.register(schema)
        for schema in build_all_camera_schemas():
            self.register(schema)
        for schema in build_all_teleop_schemas():
            self.register(schema)

        logger.info(
            f"SchemaLoader: loaded {len(self._schemas)} schemas "
            f"({len(self.list_types('robot'))} robots, "
            f"{len(self.list_types('camera'))} cameras, "
            f"{len(self.list_types('teleoperator'))} teleops)"
        )
