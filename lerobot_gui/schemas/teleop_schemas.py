"""Teleoperator schema overlays for all supported teleoperator types."""

from __future__ import annotations

from .schema_types import DeviceSchema, FieldSchema, FieldType
from .robot_schemas import _fs, _build, _calibration_dir_field


def _tid(help_: str = "Teleoperator identifier") -> FieldSchema:
    return _fs("id", "Teleoperator ID", FieldType.STRING,
               help=help_, group="general", placeholder="my_teleop")


def _piper_leader_fields() -> list[FieldSchema]:
    return [
        _tid("Piper leader arm ID (e.g. 'blue')"),
        _fs("can_name", "CAN Interface", FieldType.CAN_INTERFACE,
            group="motors", required=True, default="can_master1",
            choices=["can_master1", "can_master2", "can_slave1", "can_slave2"],
            help="CAN bus for leader arm"),
        _fs("motors", "Motor Mapping", FieldType.MOTOR_MAP,
            group="motors", advanced=True,
            default={"joint_1": [1, "agilex_piper"], "joint_2": [2, "agilex_piper"],
                     "joint_3": [3, "agilex_piper"], "joint_4": [4, "agilex_piper"],
                     "joint_5": [5, "agilex_piper"], "joint_6": [6, "agilex_piper"],
                     "gripper": [7, "agilex_piper"]}),
        _calibration_dir_field(),
    ]


def _so_leader_fields() -> list[FieldSchema]:
    return [
        _tid("SO leader arm ID"),
        _fs("port", "Serial Port", FieldType.SERIAL_PORT,
            group="general", required=True, placeholder="/dev/ttyACM1"),
        _fs("use_degrees", "Use Degrees", FieldType.BOOL,
            group="advanced", advanced=True, default=False),
    ]


def _koch_leader_fields() -> list[FieldSchema]:
    return [
        _tid("Koch leader arm ID"),
        _fs("port", "Serial Port", FieldType.SERIAL_PORT,
            group="general", required=True),
        _fs("gripper_open_pos", "Gripper Open Position", FieldType.FLOAT,
            group="control", default=50.0, min_val=0.0, max_val=100.0),
    ]


def _omx_leader_fields() -> list[FieldSchema]:
    return [
        _tid("OMX leader arm ID"),
        _fs("port", "Serial Port", FieldType.SERIAL_PORT,
            group="general", required=True),
        _fs("gripper_open_pos", "Gripper Open Position", FieldType.FLOAT,
            group="control", default=60.0),
    ]


def _bi_so_leader_fields() -> list[FieldSchema]:
    return [
        _tid("Bimanual SO leader ID"),
        _fs("left_arm_config.port", "Left Arm Port", FieldType.SERIAL_PORT,
            group="motors", required=True),
        _fs("left_arm_config.id", "Left Arm ID", FieldType.STRING, group="motors"),
        _fs("right_arm_config.port", "Right Arm Port", FieldType.SERIAL_PORT,
            group="motors", required=True),
        _fs("right_arm_config.id", "Right Arm ID", FieldType.STRING, group="motors"),
    ]


def _keyboard_fields() -> list[FieldSchema]:
    return [_tid("Keyboard teleop")]


def _keyboard_ee_fields() -> list[FieldSchema]:
    return [
        _tid("Keyboard end-effector teleop"),
        _fs("use_gripper", "Use Gripper", FieldType.BOOL,
            group="control", default=True),
    ]


def _keyboard_rover_fields() -> list[FieldSchema]:
    return [
        _tid("Keyboard rover teleop"),
        _fs("linear_speed", "Linear Speed", FieldType.FLOAT,
            group="control", default=1.0, min_val=0.0, step=0.1),
        _fs("angular_speed", "Angular Speed", FieldType.FLOAT,
            group="control", default=1.0),
        _fs("speed_increment", "Speed Increment", FieldType.FLOAT,
            group="control", default=0.1),
        _fs("turn_assist_ratio", "Turn Assist Ratio", FieldType.FLOAT,
            group="control", default=0.3),
        _fs("angular_speed_ratio", "Angular Speed Ratio", FieldType.FLOAT,
            group="control", default=0.6),
        _fs("min_linear_speed", "Min Linear Speed", FieldType.FLOAT,
            group="control", default=0.1),
        _fs("min_angular_speed", "Min Angular Speed", FieldType.FLOAT,
            group="control", default=0.05),
    ]


def _gamepad_fields() -> list[FieldSchema]:
    return [
        _tid("Gamepad teleop"),
        _fs("use_gripper", "Use Gripper", FieldType.BOOL,
            group="control", default=True),
    ]


def _phone_fields() -> list[FieldSchema]:
    return [
        _tid("Phone teleop"),
        _fs("phone_os", "Phone OS", FieldType.ENUM,
            group="general", default="ios", choices=["ios", "android"]),
        _fs("camera_offset", "Camera Offset [x,y,z]", FieldType.LIST_FLOAT,
            group="control", list_length=3, list_labels=["X", "Y", "Z"],
            help="3D offset from phone camera to end effector (m)"),
    ]


def _openarm_leader_fields() -> list[FieldSchema]:
    return [
        _tid("OpenArm leader ID"),
        _fs("port", "CAN Port", FieldType.SERIAL_PORT,
            group="general", required=True),
        _fs("can_interface", "CAN Interface", FieldType.STRING,
            group="advanced", advanced=True, default="socketcan"),
        _fs("use_can_fd", "Use CAN FD", FieldType.BOOL,
            group="advanced", advanced=True, default=True),
        _fs("can_bitrate", "CAN Bitrate", FieldType.INT,
            group="advanced", advanced=True, default=1_000_000),
        _fs("can_data_bitrate", "CAN Data Bitrate", FieldType.INT,
            group="advanced", advanced=True, default=5_000_000),
        _fs("manual_control", "Manual Control", FieldType.BOOL,
            group="control", default=False),
        _fs("motor_config", "Motor Config", FieldType.MOTOR_CONFIG_DAMIAO,
            group="motors", advanced=True),
        _fs("position_kp", "Position Kp", FieldType.LIST_FLOAT,
            group="control", advanced=True),
        _fs("position_kd", "Position Kd", FieldType.LIST_FLOAT,
            group="control", advanced=True),
    ]


def _homunculus_glove_fields() -> list[FieldSchema]:
    return [
        _tid("Homunculus glove ID"),
        _fs("port", "Serial Port", FieldType.SERIAL_PORT,
            group="general", required=True),
        _fs("side", "Hand Side", FieldType.ENUM,
            group="general", required=True, choices=["left", "right"]),
        _fs("baud_rate", "Baud Rate", FieldType.INT,
            group="advanced", advanced=True, default=115200),
    ]


def _homunculus_arm_fields() -> list[FieldSchema]:
    return [
        _tid("Homunculus arm ID"),
        _fs("port", "Serial Port", FieldType.SERIAL_PORT,
            group="general", required=True),
        _fs("baud_rate", "Baud Rate", FieldType.INT,
            group="advanced", advanced=True, default=115200),
    ]


def _unitree_g1_teleop_fields() -> list[FieldSchema]:
    return [
        _tid("Unitree G1 exoskeleton teleop ID"),
        _fs("left_arm_config.port", "Left Arm Serial Port", FieldType.SERIAL_PORT,
            group="motors"),
        _fs("left_arm_config.baud_rate", "Left Baud Rate", FieldType.INT,
            group="motors", default=115200),
        _fs("right_arm_config.port", "Right Arm Serial Port", FieldType.SERIAL_PORT,
            group="motors"),
        _fs("right_arm_config.baud_rate", "Right Baud Rate", FieldType.INT,
            group="motors", default=115200),
        _fs("frozen_joints", "Frozen Joints", FieldType.LIST_STR,
            group="control", advanced=True,
            help="Joint names to freeze during teleop"),
    ]


def _reachy2_teleop_fields() -> list[FieldSchema]:
    return [
        _tid("Reachy2 teleop ID"),
        _fs("ip_address", "IP Address", FieldType.IP_ADDRESS,
            group="network", default="localhost"),
        _fs("use_present_position", "Use Present Position", FieldType.BOOL,
            group="control", default=False),
        _fs("with_mobile_base", "Mobile Base", FieldType.BOOL,
            group="general", default=False),
        _fs("with_l_arm", "Left Arm", FieldType.BOOL, group="general", default=True),
        _fs("with_r_arm", "Right Arm", FieldType.BOOL, group="general", default=True),
        _fs("with_neck", "Neck", FieldType.BOOL, group="general", default=True),
        _fs("with_antennas", "Antennas", FieldType.BOOL, group="general", default=True),
    ]


def build_all_teleop_schemas() -> list[DeviceSchema]:
    t = "teleoperator"
    nc = False  # supports_cameras=False
    ne = False  # supports_emergency_stop=False
    return [
        _build("piper_leader", "Piper Leader", t, _piper_leader_fields(),
               "Piper leader arm (CAN bus)", supports_cameras=nc),
        _build("so100_leader", "SO-100 Leader", t, _so_leader_fields(),
               "SO-100 leader (Feetech, serial)", supports_cameras=nc),
        _build("so101_leader", "SO-101 Leader", t, _so_leader_fields(),
               "SO-101 leader (Feetech, serial)", supports_cameras=nc),
        _build("koch_leader", "Koch Leader", t, _koch_leader_fields(),
               "Koch leader (Dynamixel, serial)", supports_cameras=nc),
        _build("omx_leader", "OMX Leader", t, _omx_leader_fields(),
               supports_cameras=nc),
        _build("bi_so_leader", "Bimanual SO Leader", t, _bi_so_leader_fields(),
               supports_cameras=nc),
        _build("keyboard", "Keyboard", t, _keyboard_fields(),
               "Keyboard teleop (joint-level)",
               supports_cameras=nc, supports_emergency_stop=ne),
        _build("keyboard_ee", "Keyboard End-Effector", t, _keyboard_ee_fields(),
               supports_cameras=nc, supports_emergency_stop=ne),
        _build("keyboard_rover", "Keyboard Rover", t, _keyboard_rover_fields(),
               supports_cameras=nc, supports_emergency_stop=ne),
        _build("gamepad", "Gamepad", t, _gamepad_fields(),
               "Gamepad (joystick) teleop",
               supports_cameras=nc, supports_emergency_stop=ne),
        _build("phone", "Phone Teleop", t, _phone_fields(),
               "Smartphone teleop (iOS/Android)",
               supports_cameras=nc, supports_emergency_stop=ne),
        _build("openarm_leader", "OpenArm Leader", t, _openarm_leader_fields(),
               supports_cameras=nc),
        _build("bi_openarm_leader", "Bimanual OpenArm Leader", t,
               [_tid(), _fs("left_arm_config.port", "Left CAN Port", FieldType.SERIAL_PORT,
                            group="motors", required=True),
                _fs("right_arm_config.port", "Right CAN Port", FieldType.SERIAL_PORT,
                    group="motors", required=True)],
               supports_cameras=nc),
        _build("homunculus_glove", "Homunculus Glove", t, _homunculus_glove_fields(),
               supports_cameras=nc),
        _build("homunculus_arm", "Homunculus Arm", t, _homunculus_arm_fields(),
               supports_cameras=nc),
        _build("unitree_g1_teleop", "Unitree G1 Teleop", t, _unitree_g1_teleop_fields(),
               "Unitree G1 exoskeleton", supports_cameras=nc),
        _build("reachy2_teleoperator", "Reachy2 Teleop", t, _reachy2_teleop_fields(),
               supports_cameras=nc),
    ]
