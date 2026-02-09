from dataclasses import dataclass, field
from pathlib import Path

from lerobot.motors.piper.piper import PiperMotorsBusConfig
from lerobot.teleoperators.config import TeleoperatorConfig

@TeleoperatorConfig.register_subclass("piper_leader")
@dataclass
class PiperLeaderConfig(TeleoperatorConfig):
    calibration_dir: Path | None = Path(".cache/calibration/piper_leader")
    motors: PiperMotorsBusConfig = field(
        default_factory=lambda: PiperMotorsBusConfig(
            can_name="can_master1",
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