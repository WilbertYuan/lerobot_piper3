"""Camera schema overlays for all supported camera backends."""

from __future__ import annotations

from .schema_types import DeviceSchema, FieldSchema, FieldType
from .robot_schemas import _fs, _build


def _opencv_fields() -> list[FieldSchema]:
    return [
        _fs("index_or_path", "Device Index / Path", FieldType.DEVICE_ID,
            group="general", required=True, placeholder="0",
            help="Camera device index (int) or path to device/video file"),
        _fs("fps", "FPS", FieldType.INT,
            group="general", default=30, required=True, min_val=1, max_val=120),
        _fs("width", "Width (px)", FieldType.INT,
            group="general", default=640, required=True, min_val=160, max_val=3840),
        _fs("height", "Height (px)", FieldType.INT,
            group="general", default=480, required=True, min_val=120, max_val=2160),
        _fs("color_mode", "Color Mode", FieldType.ENUM,
            group="advanced", advanced=True, default="rgb", choices=["rgb", "bgr"]),
        _fs("rotation", "Rotation", FieldType.ENUM,
            group="advanced", advanced=True, default="no_rotation",
            choices=["no_rotation", "90", "180", "270"],
            help="Clockwise rotation"),
        _fs("warmup_s", "Warmup (s)", FieldType.INT,
            group="advanced", advanced=True, default=1, min_val=0, max_val=10),
        _fs("fourcc", "FOURCC Codec", FieldType.STRING,
            group="advanced", advanced=True, placeholder="MJPG",
            help="4-char video codec (e.g. MJPG, YUYV). Empty=auto."),
    ]


def _realsense_fields() -> list[FieldSchema]:
    return [
        _fs("serial_number_or_name", "Serial Number / Name", FieldType.STRING,
            group="general", required=True, placeholder="152222072122",
            help="RealSense serial number or friendly name"),
        _fs("fps", "FPS", FieldType.INT,
            group="general", default=30, required=True, min_val=1, max_val=90),
        _fs("width", "Width (px)", FieldType.INT,
            group="general", default=640, required=True, min_val=160, max_val=1920),
        _fs("height", "Height (px)", FieldType.INT,
            group="general", default=480, required=True, min_val=120, max_val=1080),
        _fs("use_depth", "Enable Depth", FieldType.BOOL,
            group="general", default=False, help="Enable depth stream"),
        _fs("color_mode", "Color Mode", FieldType.ENUM,
            group="advanced", advanced=True, default="rgb", choices=["rgb", "bgr"]),
        _fs("rotation", "Rotation", FieldType.ENUM,
            group="advanced", advanced=True, default="no_rotation",
            choices=["no_rotation", "90", "180", "270"]),
        _fs("warmup_s", "Warmup (s)", FieldType.INT,
            group="advanced", advanced=True, default=1),
    ]


def _zmq_fields() -> list[FieldSchema]:
    return [
        _fs("server_address", "Server Address", FieldType.IP_ADDRESS,
            group="network", required=True, help="ZMQ server IP"),
        _fs("port", "Port", FieldType.INT,
            group="network", default=5555, min_val=1024, max_val=65535),
        _fs("camera_name", "Camera Name", FieldType.STRING,
            group="general", default="zmq_camera"),
        _fs("fps", "FPS", FieldType.INT, group="general", default=30),
        _fs("width", "Width", FieldType.INT, group="general", default=640),
        _fs("height", "Height", FieldType.INT, group="general", default=480),
        _fs("color_mode", "Color Mode", FieldType.ENUM,
            group="advanced", advanced=True, default="rgb", choices=["rgb", "bgr"]),
        _fs("timeout_ms", "Timeout (ms)", FieldType.INT,
            group="advanced", advanced=True, default=5000),
        _fs("warmup_s", "Warmup (s)", FieldType.INT,
            group="advanced", advanced=True, default=1),
    ]


def _reachy2_camera_fields() -> list[FieldSchema]:
    return [
        _fs("name", "Camera Name", FieldType.ENUM,
            group="general", required=True, choices=["teleop", "depth"]),
        _fs("image_type", "Image Type", FieldType.ENUM,
            group="general", required=True,
            choices=["left", "right", "rgb", "depth"],
            help="teleop: left/right. depth: rgb/depth."),
        _fs("ip_address", "IP Address", FieldType.IP_ADDRESS,
            group="network", default="localhost"),
        _fs("port", "Port", FieldType.INT, group="network", default=50065),
        _fs("fps", "FPS", FieldType.INT, group="general"),
        _fs("width", "Width", FieldType.INT, group="general"),
        _fs("height", "Height", FieldType.INT, group="general"),
        _fs("color_mode", "Color Mode", FieldType.ENUM,
            group="advanced", advanced=True, default="rgb", choices=["rgb", "bgr"]),
    ]


def build_all_camera_schemas() -> list[DeviceSchema]:
    cam = "camera"
    return [
        _build("opencv", "OpenCV Camera", cam, _opencv_fields(),
               "USB/built-in camera via OpenCV",
               supports_cameras=False, supports_emergency_stop=False),
        _build("intelrealsense", "Intel RealSense", cam, _realsense_fields(),
               "Intel RealSense D405/D415/D435 depth camera",
               supports_cameras=False, supports_emergency_stop=False),
        _build("zmq", "ZMQ Camera", cam, _zmq_fields(),
               "Remote camera over ZMQ network",
               supports_cameras=False, supports_emergency_stop=False),
        _build("reachy2_camera", "Reachy2 Camera", cam, _reachy2_camera_fields(),
               "Reachy2 built-in cameras",
               supports_cameras=False, supports_emergency_stop=False),
    ]
