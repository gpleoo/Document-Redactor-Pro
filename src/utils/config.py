"""
Application Configuration Module.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "redactor-pro"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    """Application configuration with persistence."""
    locale: str = "it"
    theme: str = "dark"
    tesseract_path: str = ""
    default_export_dir: str = ""
    ocr_dpi: int = 300
    enabled_entities: list[str] = field(default_factory=lambda: [
        "PERSON", "FISCAL_CODE", "SSN", "IBAN",
        "EMAIL", "PHONE", "CREDIT_CARD",
    ])
    recent_files: list[str] = field(default_factory=list)
    max_recent_files: int = 10
    window_width: int = 1400
    window_height: int = 850

    def save(self):
        """Save configuration to disk."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save config: {e}")

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from disk, or return defaults."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return cls()

    def add_recent_file(self, path: str):
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:self.max_recent_files]
