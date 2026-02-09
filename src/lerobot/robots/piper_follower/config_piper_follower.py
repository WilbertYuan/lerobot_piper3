from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.motors.piper.piper import PiperMotorsBusConfig
from lerobot.robots.config import RobotConfig

@RobotConfig.register_subclass("piper_follower")
@dataclass
class PiperFollowerConfig(RobotConfig):
    motors: PiperMotorsBusConfig = field(
        default_factory=lambda: PiperMotorsBusConfig(
            can_name="can_slave1",
            motors={
                "joint_1": (1, "agilex_piper"),
                "joint_2": (2, "agilex_piper"),
                "joint_3": (3, "agilex_piper"),
                "joint_4": (4, "agilex_piper"),
                "joint_5": (5, "agilex_piper"),
                "joint_6": (6, "agilex_piper"),
                "gripper": (7, "agilex_piper"),
            }
        )
    )
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Add default RealSense cameras if none are configured
        # You can configure specific cameras by setting the cameras dict
        # Example:
        # self.cameras["laptop"] = RealSenseCameraConfig(
        #     serial_number_or_name="YOUR_SERIAL_NUMBER",
        #     fps=30,
        #     width=640,
        #     height=480
        # )
        super().__post_init__()
    