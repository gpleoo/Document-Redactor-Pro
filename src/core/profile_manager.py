"""
Profile Manager - Save/load redaction word lists.
Profiles are JSON files containing words to always redact.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

PROFILES_DIR = Path(__file__).parent.parent.parent / "resources" / "profiles"


@dataclass
class RedactionProfile:
    """A saved redaction profile with words to redact."""
    name: str = "Nuovo Profilo"
    words: list[str] = field(default_factory=list)
    description: str = ""
    redaction_style: str = "black"  # "black", "white", "custom"
    custom_text: str = ""

    def add_word(self, word: str) -> bool:
        w = word.strip()
        if w and w not in self.words:
            self.words.append(w)
            return True
        return False

    def remove_word(self, word: str) -> bool:
        w = word.strip()
        if w in self.words:
            self.words.remove(w)
            return True
        return False

    def has_word(self, word: str) -> bool:
        return word.strip() in self.words


class ProfileManager:
    """Manages saving/loading redaction profiles."""

    def __init__(self):
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile: RedactionProfile) -> bool:
        try:
            path = PROFILES_DIR / f"{self._safe_name(profile.name)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved profile: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return False

    def load_profile(self, name: str) -> RedactionProfile | None:
        try:
            path = PROFILES_DIR / f"{self._safe_name(name)}.json"
            if not path.exists():
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RedactionProfile(**data)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

    def list_profiles(self) -> list[str]:
        names = []
        if PROFILES_DIR.exists():
            for f in sorted(PROFILES_DIR.glob("*.json")):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    names.append(data.get("name", f.stem))
                except Exception:
                    names.append(f.stem)
        return names

    def delete_profile(self, name: str) -> bool:
        path = PROFILES_DIR / f"{self._safe_name(name)}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
