"""Profile / configuration persistence — save and load YAML profiles."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".visual_lerobot"
RECENT_FILE = DEFAULT_CONFIG_DIR / "recent_projects.json"


class ConfigStore:
    """Save/load device profiles and track recent projects."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

    # ---- Profile I/O ----

    def save_profile(self, name: str, data: dict[str, Any]) -> Path:
        """Save a configuration profile as YAML."""
        data["_meta"] = {
            "saved_at": datetime.now().isoformat(),
            "version": "1.0.0",
        }
        fpath = self.profiles_dir / f"{name}.yaml"
        with open(fpath, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Profile saved: {fpath}")
        return fpath

    def load_profile(self, name: str) -> dict[str, Any]:
        """Load a profile from YAML."""
        fpath = self.profiles_dir / f"{name}.yaml"
        if not fpath.exists():
            raise FileNotFoundError(f"Profile not found: {fpath}")
        with open(fpath) as f:
            data = yaml.safe_load(f) or {}
        logger.info(f"Profile loaded: {fpath}")
        return data

    def list_profiles(self) -> list[str]:
        return [p.stem for p in self.profiles_dir.glob("*.yaml")]

    def delete_profile(self, name: str) -> None:
        fpath = self.profiles_dir / f"{name}.yaml"
        if fpath.exists():
            fpath.unlink()

    # ---- Recent projects ----

    def get_recent_projects(self) -> list[dict[str, str]]:
        if not RECENT_FILE.exists():
            return []
        try:
            with open(RECENT_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def add_recent_project(self, path: str, name: str = "") -> None:
        recents = self.get_recent_projects()
        entry = {
            "path": path,
            "name": name or Path(path).name,
            "time": datetime.now().isoformat(),
        }
        recents = [r for r in recents if r["path"] != path]
        recents.insert(0, entry)
        recents = recents[:20]
        RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RECENT_FILE, "w") as f:
            json.dump(recents, f, indent=2)

    # ---- Settings ----

    def save_settings(self, settings: dict[str, Any]) -> None:
        fpath = self.config_dir / "settings.yaml"
        with open(fpath, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    def load_settings(self) -> dict[str, Any]:
        fpath = self.config_dir / "settings.yaml"
        if not fpath.exists():
            return {}
        with open(fpath) as f:
            return yaml.safe_load(f) or {}
