"""
Robot schema overlays for all supported robot types.

Covers: Piper, SO100/SO101, Koch, BiSO, Unitree G1, LeKiwi,
OpenArm, HopeJr, Reachy2, Omx, EarthRover, BiOpenArm.
"""

from __future__ import annotations

from .schema_types import DeviceSchema, FieldSchema, FieldType, SchemaGroup


def _fs(key: str, label: str, ftype: FieldType, **kw) -> FieldSchema:
    """Shorthand field schema constructor."""
    return FieldSchema(key=key, label=label, type=ftype, **kw)


def _build(
    device_type: str,
    display_name: str,
    category: str,
    fields: list[FieldSchema],
    description: str = "",
    supports_cameras: bool = True,
    supports_emergency_stop: bool = True,
) -> DeviceSchema:
    return DeviceSchema(
        version="1.0.0",
        device_type=device_type,
        device_category=category,
        display_name=display_name,
        description=description,
        fields=fields,
        supports_cameras=supports_cameras,
        supports_emergency_stop=supports_emergency_stop,
    )


# ====================================================================
# Common field definitions reused across similar robots
# ====================================================================

def _id_field(help_: str = "Unique robot identifier") -> FieldSchema:
    return _fs("id", "Robot ID", FieldType.STRING, help=help_, group="general", placeholder="my_robot")


def _port_field(help_: str = "USB serial port") -> FieldSchema:
    return _fs("port", "Serial Port", FieldType.SERIAL_PORT,
               help=help_, group="general", required=True, placeholder="/dev/ttyACM0")


def _disable_torque_field() -> FieldSchema:
    return _fs("disable_torque_on_disconnect", "Disable Torque on Disconnect",
               FieldType.BOOL, default=True, group="advanced", advanced=True,
               help="Release motor torque when disconnecting")


def _max_relative_target_field() -> FieldSchema:
    return _fs("max_relative_target", "Max Relative Target", FieldType.FLOAT,
               group="control", advanced=True, min_val=0.0, max_val=360.0,
               help="Max relative position change per step (None=no limit)")


def _cameras_field() -> FieldSchema:
    return _fs("cameras", "Cameras", FieldType.CAMERA_DICT, group="cameras",
               help="Camera configurations. JSON dict: {name: {type, ...params}}")


def _use_degrees_field() -> FieldSchema:
    return _fs("use_degrees", "Use Degrees", FieldType.BOOL, default=False,
               group="advanced", advanced=True,
               help="Report positions in degrees instead of raw values")


def _calibration_dir_field() -> FieldSchema:
    return _fs("calibration_dir", "Calibration Directory", FieldType.PATH,
               group="calibration", advanced=True,
               help="Directory to store calibration files")


# ====================================================================
# Per-robot field lists
# ====================================================================

def _piper_motors_bus_fields() -> list[FieldSchema]:
    return [
        _fs("can_name", "CAN Interface", FieldType.CAN_INTERFACE,
            help="CAN bus name. Follower: 'can_slave1', Leader: 'can_master1'",
            group="motors", required=True, default="can_slave1",
            choices=["can_slave1", "can_slave2", "can_master1", "can_master2"]),
        _fs("motors", "Motor Mapping", FieldType.MOTOR_MAP,
            help="Motor name->(index, model). Default 7 joints.",
            group="motors", advanced=True,
            default={"joint_1": [1, "agilex_piper"], "joint_2": [2, "agilex_piper"],
                     "joint_3": [3, "agilex_piper"], "joint_4": [4, "agilex_piper"],
                     "joint_5": [5, "agilex_piper"], "joint_6": [6, "agilex_piper"],
                     "gripper": [7, "agilex_piper"]}),
    ]


def _piper_follower_fields() -> list[FieldSchema]:
    return [
        _id_field("Piper follower arm ID (e.g. 'black')"),
        *_piper_motors_bus_fields(),
        _cameras_field(),
        _calibration_dir_field(),
    ]


def _so_follower_fields(motor_info: str = "Feetech STS3215") -> list[FieldSchema]:
    return [
        _id_field(f"SO-arm ID ({motor_info} motors)"),
        _port_field(f"Serial port for {motor_info} motors"),
        _disable_torque_field(),
        _max_relative_target_field(),
        _cameras_field(),
        _use_degrees_field(),
    ]


def _koch_follower_fields() -> list[FieldSchema]:
    return [
        _id_field("Koch arm ID (Dynamixel XL430/XL330 motors)"),
        _port_field("Serial port for Dynamixel motors"),
        _disable_torque_field(),
        _max_relative_target_field(),
        _cameras_field(),
        _use_degrees_field(),
    ]


def _bi_so_follower_fields() -> list[FieldSchema]:
    return [
        _id_field("Bimanual SO setup ID"),
        _fs("left_arm_config.port", "Left Arm Port", FieldType.SERIAL_PORT,
            group="motors", required=True, help="Serial port for left arm"),
        _fs("left_arm_config.id", "Left Arm ID", FieldType.STRING,
            group="motors", placeholder="left"),
        _fs("right_arm_config.port", "Right Arm Port", FieldType.SERIAL_PORT,
            group="motors", required=True, help="Serial port for right arm"),
        _fs("right_arm_config.id", "Right Arm ID", FieldType.STRING,
            group="motors", placeholder="right"),
        _fs("left_arm_config.cameras", "Left Arm Cameras", FieldType.CAMERA_DICT,
            group="cameras"),
        _fs("right_arm_config.cameras", "Right Arm Cameras", FieldType.CAMERA_DICT,
            group="cameras"),
        _disable_torque_field(),
    ]


def _unitree_g1_fields() -> list[FieldSchema]:
    return [
        _id_field("Unitree G1 humanoid ID"),
        _fs("robot_ip", "Robot IP Address", FieldType.IP_ADDRESS,
            group="network", required=True, default="192.168.123.164",
            help="IP address of the Unitree G1"),
        _fs("is_simulation", "Simulation Mode", FieldType.BOOL,
            group="general", default=True, help="Run in simulation"),
        _fs("control_dt", "Control Timestep (s)", FieldType.FLOAT,
            group="control", default=0.004, min_val=0.001, max_val=0.1, step=0.001,
            help="Control loop period (default 1/250=4ms)"),
        _fs("gravity_compensation", "Gravity Compensation", FieldType.BOOL,
            group="control", default=False),
        _fs("kp", "Position Gains (Kp)", FieldType.LIST_FLOAT,
            group="control", advanced=True, list_length=29,
            help="Per-joint proportional gains (29 values)"),
        _fs("kd", "Damping Gains (Kd)", FieldType.LIST_FLOAT,
            group="control", advanced=True, list_length=29,
            help="Per-joint damping gains (29 values)"),
        _fs("default_positions", "Default Positions", FieldType.LIST_FLOAT,
            group="control", advanced=True, list_length=29),
        _cameras_field(),
    ]


def _lekiwi_fields() -> list[FieldSchema]:
    return [
        _id_field("LeKiwi mobile manipulator ID"),
        _port_field("Serial port for Feetech motors"),
        _disable_torque_field(),
        _max_relative_target_field(),
        _cameras_field(),
        _use_degrees_field(),
    ]


def _lekiwi_client_fields() -> list[FieldSchema]:
    return [
        _id_field("LeKiwi remote client ID"),
        _fs("remote_ip", "Remote IP", FieldType.IP_ADDRESS,
            group="network", required=True, help="IP of LeKiwi host"),
        _fs("port_zmq_cmd", "ZMQ Command Port", FieldType.INT,
            group="network", default=5555, min_val=1024, max_val=65535),
        _fs("port_zmq_observations", "ZMQ Observation Port", FieldType.INT,
            group="network", default=5556, min_val=1024, max_val=65535),
        _fs("teleop_keys", "Teleop Key Mapping", FieldType.TELEOP_KEYS,
            group="control", help="Keyboard keys for movement"),
        _cameras_field(),
        _fs("polling_timeout_ms", "Polling Timeout (ms)", FieldType.INT,
            group="advanced", advanced=True, default=15),
        _fs("connect_timeout_s", "Connect Timeout (s)", FieldType.INT,
            group="advanced", advanced=True, default=5),
    ]


def _openarm_follower_fields() -> list[FieldSchema]:
    return [
        _id_field("OpenArm ID (Damiao motors, CAN FD)"),
        _port_field("CAN interface port"),
        _fs("side", "Arm Side", FieldType.ENUM,
            group="general", choices=["", "left", "right"],
            help="Arm side for bimanual setups"),
        _fs("can_interface", "CAN Interface Type", FieldType.STRING,
            group="advanced", advanced=True, default="socketcan"),
        _fs("use_can_fd", "Use CAN FD", FieldType.BOOL,
            group="advanced", advanced=True, default=True,
            help="Enable CAN Flexible Data-rate"),
        _fs("can_bitrate", "CAN Bitrate", FieldType.INT,
            group="advanced", advanced=True, default=1_000_000),
        _fs("can_data_bitrate", "CAN Data Bitrate", FieldType.INT,
            group="advanced", advanced=True, default=5_000_000),
        _disable_torque_field(),
        _max_relative_target_field(),
        _fs("motor_config", "Motor Configuration", FieldType.MOTOR_CONFIG_DAMIAO,
            group="motors", advanced=True,
            help="Motor name->(send_id, recv_id, type) for Damiao motors"),
        _fs("position_kp", "Position Kp Gains", FieldType.LIST_FLOAT,
            group="control", advanced=True, help="Per-joint Kp gains"),
        _fs("position_kd", "Position Kd Gains", FieldType.LIST_FLOAT,
            group="control", advanced=True, help="Per-joint Kd gains"),
        _fs("joint_limits", "Joint Limits", FieldType.JOINT_LIMITS,
            group="control", advanced=True,
            help="Per-joint (min, max) in radians"),
        _cameras_field(),
    ]


def _hope_jr_hand_fields() -> list[FieldSchema]:
    return [
        _id_field("Hope Jr hand ID"),
        _port_field("Serial port for SCS0009 hand motors"),
        _fs("side", "Hand Side", FieldType.ENUM,
            group="general", required=True, choices=["left", "right"]),
        _disable_torque_field(),
        _cameras_field(),
    ]


def _hope_jr_arm_fields() -> list[FieldSchema]:
    return [
        _id_field("Hope Jr arm ID"),
        _port_field("Serial port for STS3250/SM8512BL arm motors"),
        _disable_torque_field(),
        _max_relative_target_field(),
        _cameras_field(),
    ]


def _reachy2_fields() -> list[FieldSchema]:
    return [
        _id_field("Reachy2 robot ID"),
        _fs("ip_address", "Robot IP Address", FieldType.IP_ADDRESS,
            group="network", default="localhost"),
        _fs("port", "gRPC Port", FieldType.INT,
            group="network", default=50051),
        _max_relative_target_field(),
        _disable_torque_field(),
        _fs("use_external_commands", "Use External Commands", FieldType.BOOL,
            group="advanced", advanced=True, default=False),
        _fs("with_mobile_base", "With Mobile Base", FieldType.BOOL,
            group="general", default=False),
        _fs("with_l_arm", "With Left Arm", FieldType.BOOL,
            group="general", default=True),
        _fs("with_r_arm", "With Right Arm", FieldType.BOOL,
            group="general", default=True),
        _fs("with_neck", "With Neck", FieldType.BOOL,
            group="general", default=True),
        _fs("with_antennas", "With Antennas", FieldType.BOOL,
            group="general", default=True),
        _fs("camera_width", "Camera Width", FieldType.INT,
            group="cameras", default=640),
        _fs("camera_height", "Camera Height", FieldType.INT,
            group="cameras", default=480),
        _cameras_field(),
    ]


def _earthrover_fields() -> list[FieldSchema]:
    return [
        _id_field("EarthRover Mini+ ID"),
        _fs("sdk_url", "SDK API URL", FieldType.STRING,
            group="network", default="http://localhost:8000",
            help="HTTP URL for the EarthRover SDK"),
    ]


# ====================================================================
# Build all robot schemas
# ====================================================================

def build_all_robot_schemas() -> list[DeviceSchema]:
    return [
        _build("piper_follower", "Piper Follower", "robot",
               _piper_follower_fields(),
               "AgileX Piper 6-DOF arm + gripper (CAN bus)"),

        _build("so100_follower", "SO-100 Follower", "robot",
               _so_follower_fields("Feetech STS3215"),
               "SO-100 5-DOF arm + gripper (Feetech, serial)"),

        _build("so101_follower", "SO-101 Follower", "robot",
               _so_follower_fields("Feetech STS3215"),
               "SO-101 arm (Feetech STS3215, serial)"),

        _build("koch_follower", "Koch Follower", "robot",
               _koch_follower_fields(),
               "Koch v1.1 arm (Dynamixel XL430/XL330, serial)"),

        _build("omx_follower", "OMX Follower", "robot",
               _so_follower_fields("serial"),
               "OMX arm (serial connection)"),

        _build("bi_so_follower", "Bimanual SO Follower", "robot",
               _bi_so_follower_fields(),
               "Bimanual setup with two SO-100 follower arms"),

        _build("unitree_g1", "Unitree G1", "robot",
               _unitree_g1_fields(),
               "Unitree G1 humanoid (29 DOF, ZMQ network)"),

        _build("lekiwi", "LeKiwi", "robot",
               _lekiwi_fields(),
               "LeKiwi mobile manipulator (6-DOF arm + 3 wheels)"),

        _build("lekiwi_client", "LeKiwi Client", "robot",
               _lekiwi_client_fields(),
               "Remote client for LeKiwi (ZMQ)"),

        _build("openarm_follower", "OpenArm Follower", "robot",
               _openarm_follower_fields(),
               "OpenArm (Damiao DM8009/DM4340/DM4310, CAN FD)"),

        _build("bi_openarm_follower", "Bimanual OpenArm", "robot",
               [_id_field("Bimanual OpenArm ID"),
                _fs("left_arm_config.port", "Left Arm CAN Port", FieldType.SERIAL_PORT,
                    group="motors", required=True),
                _fs("right_arm_config.port", "Right Arm CAN Port", FieldType.SERIAL_PORT,
                    group="motors", required=True),
                _cameras_field()],
               "Bimanual OpenArm (two Damiao arms)"),

        _build("hope_jr_hand", "Hope Jr Hand", "robot",
               _hope_jr_hand_fields(),
               "Hope Junior dexterous hand (Feetech SCS0009)"),

        _build("hope_jr_arm", "Hope Jr Arm", "robot",
               _hope_jr_arm_fields(),
               "Hope Junior arm (Feetech STS3250/SM8512BL)"),

        _build("reachy2", "Reachy2", "robot",
               _reachy2_fields(),
               "Pollen Robotics Reachy2 (gRPC network)"),

        _build("earthrover_mini_plus", "EarthRover Mini+", "robot",
               _earthrover_fields(),
               "EarthRover Mini+ mobile robot (HTTP API)",
               supports_cameras=False),
    ]
