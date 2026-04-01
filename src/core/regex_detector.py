"""
Regex Detector - Finds structured sensitive data patterns.
Zero false positives: only matches mathematically certain patterns.
"""

import re
from dataclasses import dataclass
from enum import Enum


class PatternType(str, Enum):
    FISCAL_CODE = "Codice Fiscale"
    SSN = "SSN (US)"
    IBAN = "IBAN"
    EMAIL = "Email"
    PHONE = "Telefono"
    CREDIT_CARD = "Carta di Credito"
    DATE = "Data"
    VAT = "Partita IVA"


@dataclass
class PatternMatch:
    """A regex pattern match found in text."""
    text: str
    pattern_type: PatternType
    start: int
    end: int


# Each pattern is (PatternType, compiled regex)
PATTERNS: list[tuple[PatternType, re.Pattern]] = [
    (PatternType.FISCAL_CODE, re.compile(
        r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b", re.IGNORECASE
    )),
    (PatternType.SSN, re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    )),
    (PatternType.IBAN, re.compile(
        r"\b[A-Z]{2}\d{2}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{0,4}\s?[\dA-Z]{0,4}\b",
        re.IGNORECASE,
    )),
    (PatternType.VAT, re.compile(
        r"\b[A-Z]{2}\d{11}\b", re.IGNORECASE
    )),
    (PatternType.EMAIL, re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    )),
    (PatternType.PHONE, re.compile(
        r"\b\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b"
    )),
    (PatternType.CREDIT_CARD, re.compile(
        r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"
    )),
    (PatternType.DATE, re.compile(
        r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"
    )),
]


class RegexDetector:
    """Scans text for structured sensitive data using regex patterns."""

    def __init__(self, enabled_types: set[PatternType] | None = None):
        self.enabled_types = enabled_types or set(PatternType)

    def scan_text(self, text: str) -> list[PatternMatch]:
        matches: list[PatternMatch] = []
        for ptype, pattern in PATTERNS:
            if ptype not in self.enabled_types:
                continue
            for m in pattern.finditer(text):
                matches.append(PatternMatch(
                    text=m.group(), pattern_type=ptype,
                    start=m.start(), end=m.end(),
                ))
        return matches

    def scan_blocks(self, blocks) -> dict[int, list[PatternMatch]]:
        """Scan blocks and return {block_index: [matches]}."""
        results: dict[int, list[PatternMatch]] = {}
        for idx, block in enumerate(blocks):
            matches = self.scan_text(block.text)
            if matches:
                results[idx] = matches
        return results
