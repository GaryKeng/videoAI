"""
Application settings persistence.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import VIDEOAI_HOME


class SettingsManager:
    """Manage application settings persistence."""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or VIDEOAI_HOME / "settings.json"
        self.settings: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Load settings from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = {}
        else:
            self.settings = self._get_defaults()

    def save(self):
        """Save settings to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        keys = key.split(".")
        value = self.settings

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        """Set setting value."""
        keys = key.split(".")
        settings = self.settings

        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]

        settings[keys[-1]] = value

    def reset(self):
        """Reset to defaults."""
        self.settings = self._get_defaults()
        self.save()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            "whisper_model": "large-v3",
            "whisper_language": "zh",
            "vad_threshold": 0.5,
            "max_pause_duration": 0.8,
            "repetition_threshold": 0.7,
            "match_threshold": 0.5,
            "max_overlay_width": 0.4,
            "enable_learning": True,
            "recent_projects": [],
            "window_geometry": {
                "width": 1400,
                "height": 900,
                "x": None,
                "y": None
            }
        }

    def add_recent_project(self, project_name: str, max_recent: int = 10):
        """Add project to recent list."""
        recent = self.get("recent_projects", [])

        # Remove if exists
        if project_name in recent:
            recent.remove(project_name)

        # Add to front
        recent.insert(0, project_name)

        # Trim to max
        self.settings["recent_projects"] = recent[:max_recent]

    def get_recent_projects(self) -> list:
        """Get recent project list."""
        return self.get("recent_projects", [])


# Global settings instance
settings_manager = SettingsManager()
