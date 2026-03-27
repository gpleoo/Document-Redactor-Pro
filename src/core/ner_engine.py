"""
NER Engine Module - Named Entity Recognition for sensitive data detection.
Uses spaCy and Presidio for offline entity recognition with support for
multiple locales (Italian fiscal codes, US SSN, IBAN, etc.).
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not installed; NER will use regex-only fallback")

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning("Presidio not installed; using regex-only entity detection")


class EntityType(str, Enum):
    PERSON = "PERSON"
    FISCAL_CODE = "FISCAL_CODE"
    SSN = "SSN"
    IBAN = "IBAN"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    CREDIT_CARD = "CREDIT_CARD"
    SIGNATURE = "SIGNATURE"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    CUSTOM = "CUSTOM"


@dataclass
class DetectedEntity:
    """A sensitive entity detected in the text."""
    text: str
    entity_type: EntityType
    start: int
    end: int
    score: float = 0.0
    source_block_indices: list[int] = None

    def __post_init__(self):
        if self.source_block_indices is None:
            self.source_block_indices = []


REGEX_PATTERNS: dict[EntityType, list[re.Pattern]] = {
    EntityType.FISCAL_CODE: [
        re.compile(
            r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b",
            re.IGNORECASE,
        ),
    ],
    EntityType.SSN: [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    ],
    EntityType.IBAN: [
        re.compile(
            r"\b[A-Z]{2}\d{2}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{0,4}\s?[\dA-Z]{0,4}\b",
            re.IGNORECASE,
        ),
    ],
    EntityType.EMAIL: [
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"),
    ],
    EntityType.PHONE: [
        re.compile(r"\b\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b"),
    ],
    EntityType.CREDIT_CARD: [
        re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    ],
    EntityType.DATE_OF_BIRTH: [
        re.compile(r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"),
    ],
}

PRESIDIO_TO_ENTITY: dict[str, EntityType] = {
    "PERSON": EntityType.PERSON,
    "EMAIL_ADDRESS": EntityType.EMAIL,
    "PHONE_NUMBER": EntityType.PHONE,
    "IBAN_CODE": EntityType.IBAN,
    "CREDIT_CARD": EntityType.CREDIT_CARD,
    "US_SSN": EntityType.SSN,
    "IT_FISCAL_CODE": EntityType.FISCAL_CODE,
    "LOCATION": EntityType.LOCATION,
    "ORGANIZATION": EntityType.ORGANIZATION,
    "DATE_TIME": EntityType.DATE_OF_BIRTH,
    "NRP": EntityType.PERSON,
}


class NEREngine:
    """Offline Named Entity Recognition engine combining regex patterns,
    spaCy NER, and Presidio analyzers."""

    SUPPORTED_LOCALES = ["it", "en", "de", "fr", "es"]
    DEFAULT_SPACY_MODELS = {
        "it": "it_core_news_sm",
        "en": "en_core_web_sm",
        "de": "de_core_news_sm",
        "fr": "fr_core_news_sm",
        "es": "es_core_news_sm",
    }

    def __init__(self, locale: str = "it", enabled_entities: Optional[set[EntityType]] = None):
        self._locale = locale if locale in self.SUPPORTED_LOCALES else "it"
        self._enabled_entities = enabled_entities or set(EntityType)
        self._nlp = None
        self._analyzer = None
        self._initialize()

    def _initialize(self):
        """Load spaCy model and Presidio analyzer."""
        self._loaded_model_name = None

        if SPACY_AVAILABLE:
            model_name = self.DEFAULT_SPACY_MODELS.get(self._locale, "en_core_web_sm")
            try:
                self._nlp = spacy.load(model_name)
                self._loaded_model_name = model_name
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(
                    f"spaCy model '{model_name}' not found. "
                    f"Install it with: python -m spacy download {model_name}"
                )
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                    self._loaded_model_name = "en_core_web_sm"
                except OSError:
                    logger.warning("No spaCy model available; using regex-only mode")

        if PRESIDIO_AVAILABLE and self._nlp is not None and self._loaded_model_name:
            try:
                nlp_engine = SpacyNlpEngine(
                    models=[{"lang_code": self._locale, "model_name": self._loaded_model_name}]
                )
                self._analyzer = AnalyzerEngine(
                    nlp_engine=nlp_engine,
                    supported_languages=[self._locale],
                )
                logger.info("Presidio analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Presidio (will use spaCy + regex): {e}")
                self._analyzer = None

    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        if value != self._locale and value in self.SUPPORTED_LOCALES:
            self._locale = value
            self._initialize()

    @property
    def enabled_entities(self) -> set[EntityType]:
        return self._enabled_entities

    @enabled_entities.setter
    def enabled_entities(self, value: set[EntityType]) -> None:
        self._enabled_entities = value

    def analyze_text(self, text: str) -> list[DetectedEntity]:
        """Run full NER analysis on a text string.

        Combines regex pattern matching, spaCy NER, and Presidio analysis,
        deduplicating overlapping entities.
        """
        entities: list[DetectedEntity] = []

        entities.extend(self._regex_scan(text))

        if self._nlp is not None:
            entities.extend(self._spacy_scan(text))

        if self._analyzer is not None:
            entities.extend(self._presidio_scan(text))

        entities = self._deduplicate(entities)
        entities = [e for e in entities if e.entity_type in self._enabled_entities]

        return sorted(entities, key=lambda e: e.start)

    def analyze_blocks(self, blocks) -> list[DetectedEntity]:
        """Analyze a list of TextBlock objects and map entities back to block indices."""
        full_text_parts = []
        block_offsets = []
        offset = 0

        for idx, block in enumerate(blocks):
            full_text_parts.append(block.text)
            block_offsets.append((offset, offset + len(block.text), idx))
            offset += len(block.text) + 1  # +1 for space separator

        full_text = " ".join(full_text_parts)
        entities = self.analyze_text(full_text)

        for entity in entities:
            entity.source_block_indices = []
            for b_start, b_end, b_idx in block_offsets:
                if entity.start < b_end and entity.end > b_start:
                    entity.source_block_indices.append(b_idx)

        return entities

    def _regex_scan(self, text: str) -> list[DetectedEntity]:
        """Scan text using regex patterns for known entity formats."""
        entities: list[DetectedEntity] = []
        for entity_type, patterns in REGEX_PATTERNS.items():
            if entity_type not in self._enabled_entities:
                continue
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entities.append(DetectedEntity(
                        text=match.group(),
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        score=0.85,
                    ))
        return entities

    def _spacy_scan(self, text: str) -> list[DetectedEntity]:
        """Scan text using spaCy NER model."""
        if self._nlp is None:
            return []

        doc = self._nlp(text)
        entities: list[DetectedEntity] = []
        spacy_map = {
            "PER": EntityType.PERSON,
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
        }

        for ent in doc.ents:
            entity_type = spacy_map.get(ent.label_)
            if entity_type and entity_type in self._enabled_entities:
                entities.append(DetectedEntity(
                    text=ent.text,
                    entity_type=entity_type,
                    start=ent.start_char,
                    end=ent.end_char,
                    score=0.75,
                ))
        return entities

    def _presidio_scan(self, text: str) -> list[DetectedEntity]:
        """Scan text using Presidio analyzer."""
        if self._analyzer is None:
            return []

        try:
            results = self._analyzer.analyze(
                text=text,
                language=self._locale,
            )
        except Exception as e:
            logger.warning(f"Presidio analysis failed: {e}")
            return []

        entities: list[DetectedEntity] = []
        for result in results:
            entity_type = PRESIDIO_TO_ENTITY.get(result.entity_type)
            if entity_type and entity_type in self._enabled_entities:
                entities.append(DetectedEntity(
                    text=text[result.start:result.end],
                    entity_type=entity_type,
                    start=result.start,
                    end=result.end,
                    score=result.score,
                ))
        return entities

    def _deduplicate(self, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        """Remove overlapping entities, keeping the highest-scoring one."""
        if not entities:
            return []

        sorted_entities = sorted(entities, key=lambda e: (-e.score, e.start))
        kept: list[DetectedEntity] = []

        for entity in sorted_entities:
            overlap = False
            for existing in kept:
                if entity.start < existing.end and entity.end > existing.start:
                    overlap = True
                    break
            if not overlap:
                kept.append(entity)

        return kept
