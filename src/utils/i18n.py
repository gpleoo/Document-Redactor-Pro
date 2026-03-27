"""
Internationalization Module - Loads locale strings from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).parent.parent.parent / "resources" / "locales"


class I18n:
    """Simple i18n system loading strings from JSON locale files."""

    def __init__(self, locale: str = "en"):
        self._locale = locale
        self._strings: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._load_locale("en")
        self._fallback = self._strings.copy()
        if locale != "en":
            self._load_locale(locale)

    def _load_locale(self, locale: str):
        path = LOCALES_DIR / f"{locale}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._strings = json.load(f)
                logger.info(f"Loaded locale: {locale}")
            except Exception as e:
                logger.warning(f"Failed to load locale '{locale}': {e}")
        else:
            logger.warning(f"Locale file not found: {path}")

    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        self._locale = value
        self._load_locale(value)

    def t(self, key: str, **kwargs) -> str:
        """Translate a key to the current locale string.

        Supports format placeholders: t("hello", name="World") -> "Hello, World!"
        """
        text = self._strings.get(key, self._fallback.get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text

    def get_available_locales(self) -> list[str]:
        """Return list of available locale codes."""
        locales = []
        if LOCALES_DIR.exists():
            for f in LOCALES_DIR.glob("*.json"):
                locales.append(f.stem)
        return sorted(locales)
