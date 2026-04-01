"""
NER Engine Module - Named Entity Recognition for sensitive data detection.
Uses spaCy and Presidio for offline entity recognition with support for
multiple locales (Italian fiscal codes, US SSN, IBAN, etc.).

DESIGN: The Italian spaCy small model produces massive false positives on
technical/legal documents. This engine uses a STRICT filtering approach:
- Regex patterns for structured data (fiscal codes, IBAN, SSN, email, phone, etc.)
- spaCy NER ONLY for multi-word proper names (e.g. "Mario Rossi")
- Single-word entities must be in a known names list or have very high confidence
- Aggressive Italian vocabulary filter to reject common words
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
        re.compile(r"\b\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b"),
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

# ---------------------------------------------------------------------------
# AGGRESSIVE false-positive filtering
# ---------------------------------------------------------------------------

# Every Italian word that is NOT a proper noun. This is intentionally huge.
# If a word appears here, it will NEVER be detected as PERSON/ORG/LOCATION.
_COMMON_IT = {
    # Function words (articles, prepositions, conjunctions, pronouns)
    "il", "lo", "la", "le", "gli", "i", "l", "un", "uno", "una",
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
    "del", "dello", "della", "delle", "dei", "degli",
    "al", "allo", "alla", "alle", "ai", "agli",
    "dal", "dallo", "dalla", "dalle", "dai", "dagli",
    "nel", "nello", "nella", "nelle", "nei", "negli",
    "sul", "sullo", "sulla", "sulle", "sui", "sugli",
    "e", "o", "ma", "se", "che", "ed", "od", "né",
    "oppure", "ovvero", "nonché", "quindi", "perché", "quando",
    "si", "ci", "ne", "mi", "ti", "vi", "li",
    "questo", "quello", "questa", "quella", "questi", "quelli",
    "quale", "quali", "quanto", "quanta", "quanti", "quante",
    "chi", "cui", "dove", "come", "cosa",
    "non", "anche", "ancora", "già", "più", "meno",
    "molto", "poco", "tutto", "ogni", "altro", "altra",
    "stesso", "stessa", "suo", "sua", "suoi", "sue", "loro",
    "sono", "è", "ha", "hanno", "essere", "avere", "fare",
    "no", "sì",
    # Roman numerals
    "ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii",
    # Abbreviations
    "n", "nr", "pag", "ing", "arch", "geom", "dott", "sig", "spett",
    "srl", "spa", "snc", "sas", "soc", "coop",
    "prot", "rif", "det", "all", "cap", "tel", "fax", "iso",

    # ===== Common Italian nouns/adjectives/verbs (NOT proper nouns) =====
    # These are the words that spaCy falsely tags as PERSON/ORG/LOC

    # Technical / Engineering / HVAC / Mechanical
    "condensazione", "condensata", "condensante", "motocondensante",
    "refrigerante", "refrigeratore", "refrigerazione",
    "compressore", "compressori", "ventilatore", "ventilatori", "ventilazione",
    "riscaldamento", "raffreddamento", "deumidificazione", "climatizzazione",
    "caldaia", "caldaie", "bruciatore", "bruciatori",
    "scambiatore", "termico", "termica", "termici", "termiche",
    "potenza", "portata", "pressione", "temperatura", "rendimento",
    "resa", "assorbita", "assorbimento", "frigorifera", "frigorifero",
    "basamento", "pannello", "pannelli", "comando", "controllo",
    "impostazione", "visualizzazione", "monitoraggio", "programmazione",
    "segnalazione", "memorizzazione", "regolazione", "alimentazione",
    "tubazione", "tubazioni", "raccordo", "raccordi", "valvola", "valvole",
    "giunto", "giunti", "derivazione", "collegamento", "collegamenti",
    "isolamento", "rivestimento", "verniciato", "verniciatura",
    "metallica", "metallico", "metallici", "metalliche",
    "fibra", "silicio", "alluminio", "acciaio", "inox", "rame",
    "poliuretano", "polietilene", "policarbonato",
    "ermetico", "ermetici", "scroll", "inverter",
    "espansione", "diretta", "diretto", "diretti",
    "recupero", "calore", "aria", "acqua", "gas", "fluido",
    "flusso", "volume", "massa", "peso", "densità",
    "interno", "interna", "interni", "interne",
    "esterno", "esterna", "esterni", "esterne",
    "unità", "sistema", "sistemi", "impianto", "impianti",
    "circuito", "circuiti", "componente", "componenti",
    "dispositivo", "dispositivi", "apparecchio", "apparecchiatura",
    "motore", "motori", "pompa", "pompe", "elettrico", "elettrica",
    "elettrici", "elettriche", "elettronico", "elettronica",
    "centrale", "centrali", "locale", "locali",
    "sonora", "sonoro", "acustico", "acustica",
    "cassetta", "mandata", "ripresa", "ritorno",
    "batteria", "resistenza", "condensatore", "evaporatore",
    "generatore", "generatori", "trasformatore",
    "superficie", "superficie", "diametro", "lunghezza", "altezza",
    "larghezza", "spessore", "sezione", "dimensione", "dimensioni",

    # Construction / Architecture
    "opera", "opere", "lavori", "lavoro", "cantiere",
    "committente", "concorrente", "appaltante", "subappalto",
    "appalto", "gara", "progetto", "progettazione",
    "direzione", "impresa", "ditta", "contratto", "capitolato",
    "disciplinare", "bando", "offerta", "aggiudicazione",
    "completamento", "padiglione", "struttura", "edificio",
    "fornitura", "forniture", "lavorazioni", "lavorazione",
    "carpenteria", "lamiera", "armatura", "calcestruzzo", "cemento",
    "solaio", "solai", "pianerottolo", "pianerottoli",
    "copertura", "fondazione", "fondazioni", "pilastro", "pilastri",
    "trave", "travi", "muratura", "pavimento", "pavimentazione",
    "intonaco", "tinteggiatura", "impermeabilizzazione",
    "demolizione", "scavo", "riempimento", "getto",
    "coibentato", "coibentazione", "guscio", "chiuse",
    "ricotto", "variabile", "cellule",

    # Legal / Administrative / Bureaucratic
    "procedura", "esecuzione", "collaudo", "certificato", "certificata",
    "attestazione", "categoria", "classifica", "importo",
    "ribasso", "cauzione", "garanzia", "variante",
    "riserva", "penale", "termine", "scadenza", "consegna",
    "ultimazione", "provvista", "campioni", "campione", "prelievo",
    "amministrazione", "responsabile", "procedimento",
    "interregionale", "pubbliche", "pubblico", "provveditorato",
    "autorità", "vigilanza", "regolamento", "decreto", "legge",
    "articolo", "comma", "codice", "normativa", "disposizione",
    "prescrizione", "requisito", "documentazione", "verbale",
    "stazione", "società", "ente", "ministero",
    "dipartimento", "servizio", "ufficio",
    "delibera", "determina", "ordinanza", "circolare",

    # Roles / Titles (generic, not names)
    "ingegnere", "architetto", "geometra", "direttore", "presidente",
    "segretario", "commissario", "funzionario", "tecnico", "ispettore",
    "coordinatore", "collaudatore", "progettista",

    # Document / Table structure
    "oggetto", "data", "firma", "timbro", "allegato", "allegati",
    "pagina", "foglio", "copia", "originale", "conforme",
    "intestazione", "protocollo", "riferimento",
    "lista", "elenco", "tabella", "quadro", "riepilogo", "sommario",
    "sigla", "tipo", "zona", "intervento", "numero", "parte",
    "descrizione", "prezzo", "unitario", "complessivo",
    "lordo", "netto", "totale", "totali", "subtotale",
    "parziale", "generale", "specifico", "sommano",

    # Common adjectives / adverbs
    "nuovo", "nuova", "nuovi", "nuove",
    "vecchio", "vecchia", "vecchi", "vecchie",
    "precedente", "successivo", "seguente",
    "presente", "corrente", "attuale",
    "primo", "secondo", "terzo", "quarto", "quinto",
    "previste", "previsto", "prevista", "previsti",
    "eventuale", "eventuali", "anomalia", "anomalie",
    "necessario", "necessaria", "necessari", "necessarie",
    "disponibile", "disponibili", "funzionale", "funzionali",
    "principale", "principali", "supplementare", "supplementari",
    "aggiuntivo", "aggiuntiva", "aggiuntivi", "aggiuntive",
    "massimo", "massima", "minimo", "minima",
    "medio", "media", "nominale", "nominali",
    "possibile", "possibili", "impossibile",
    "sufficiente", "insufficiente",
    "idoneo", "idonea", "conforme", "difforme",
    "superiore", "inferiore", "maggiore", "minore",
    "alto", "alta", "basso", "bassa",
    "lungo", "lunga", "corto", "corta",
    "largo", "larga", "stretto", "stretta",
    "pieno", "piena", "vuoto", "vuota",
    "aperto", "aperta", "chiuso", "chiusa",
    "colorato", "colorata", "cromato", "cromata",
    "doppio", "doppia", "triplo", "singolo", "singola",
    "verticale", "orizzontale", "circolare", "rettangolare",
    "fisso", "fissi", "mobile", "mobili",
    "utilizzato", "utilizzata", "realizzato", "realizzata",

    # Common verbs / participles
    "posto", "posta", "posti", "poste",
    "costituita", "costituito", "dotata", "dotato",
    "composta", "composto", "comprese", "compreso", "compresi",
    "collegato", "collegata", "installato", "installata",
    "fornito", "fornita", "forniti", "fornite",
    "previsto", "prevista", "previsti", "previste",
    "riscontrato", "riscontrata", "riscontrate", "riscontrati",
    "avvenuto", "avvenuta", "avvenute", "avvenuti",
    "impostare", "impostato", "impostata",

    # Units / Measures
    "cadauno", "cadauna", "pezzo", "pezzi",
    "metro", "metri", "centimetro", "millimetro",
    "litro", "litri", "chilogrammo", "grammo",
    "watt", "kilowatt", "volt", "ampere",

    # Common nouns
    "tipo", "modo", "caso", "fine", "punto", "luogo", "tempo",
    "giorno", "mese", "anno", "ora", "minuto",
    "base", "piano", "lato", "centro", "bordo", "margine",
    "fase", "stato", "livello", "grado", "classe", "gruppo",
    "serie", "marca", "modello", "versione", "formato",
    "funzione", "funzioni", "posizione", "condizione", "condizioni",
    "caratteristica", "caratteristiche", "proprietà",
    "informazione", "informazioni", "indicazione", "indicazioni",
    "orologio", "display", "cristalli", "liquidi",
    "round", "flow", "vie",

    # More HVAC / mechanical from user's document
    "polvere", "basamento", "manutenzione",
    "combustione", "metano", "frigorifero", "frigorifera",
    "collegabili", "timer", "caldo", "freddo",
    "remoto", "centralizzato", "giornaliera",
}

COMMON_WORDS_IT = frozenset(_COMMON_IT)

# Minimum confidence score - MUCH higher than before
SCORE_THRESHOLDS: dict[EntityType, float] = {
    EntityType.PERSON: 0.65,
    EntityType.ORGANIZATION: 0.65,
    EntityType.LOCATION: 0.60,
}
DEFAULT_SCORE_THRESHOLD = 0.30


def _is_proper_noun(word: str) -> bool:
    """Check if a word looks like a proper noun (Title Case, not all-caps)."""
    if not word or len(word) < 2:
        return False
    return word[0].isupper() and not word.isupper() and not word.islower()


def _is_common_word(word: str) -> bool:
    """Check if a word is a common Italian word (not a proper noun)."""
    return word.lower() in COMMON_WORDS_IT


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
        """Run full NER analysis on a text string."""
        entities: list[DetectedEntity] = []

        entities.extend(self._regex_scan(text))

        if self._nlp is not None:
            entities.extend(self._spacy_scan(text))

        if self._analyzer is not None:
            entities.extend(self._presidio_scan(text))

        entities = self._deduplicate(entities)
        entities = self._filter_false_positives(entities)
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
            offset += len(block.text) + 1

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
                        score=0.95,
                    ))
        return entities

    def _spacy_scan(self, text: str) -> list[DetectedEntity]:
        """Scan text using spaCy NER - STRICT filtering at source."""
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
            if not entity_type or entity_type not in self._enabled_entities:
                continue

            text_clean = ent.text.strip()
            words = text_clean.split()

            # STRICT: reject any entity where ALL words are common vocabulary
            if all(_is_common_word(w) for w in words):
                continue

            # STRICT: reject single words that are common or too short
            if len(words) == 1:
                w = words[0]
                if len(w) < 4:
                    continue
                if _is_common_word(w):
                    continue
                if w.isupper() or w.islower():
                    continue
                # Single word must be Title Case and NOT in common words
                if not _is_proper_noun(w):
                    continue
                score = 0.55
            else:
                # Multi-word: need at least one proper noun that isn't common
                real_names = [w for w in words if _is_proper_noun(w) and not _is_common_word(w)]
                if not real_names:
                    continue
                score = 0.70

            entities.append(DetectedEntity(
                text=text_clean,
                entity_type=entity_type,
                start=ent.start_char,
                end=ent.end_char,
                score=score,
            ))
        return entities

    def _presidio_scan(self, text: str) -> list[DetectedEntity]:
        """Scan text using Presidio analyzer - pre-filtered."""
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
            if result.score < 0.40:
                continue
            entity_type = PRESIDIO_TO_ENTITY.get(result.entity_type)
            if entity_type and entity_type in self._enabled_entities:
                detected_text = text[result.start:result.end].strip()
                # Skip common words for NLP-based entity types
                if entity_type in (EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION):
                    words = detected_text.split()
                    if all(_is_common_word(w) for w in words):
                        continue
                entities.append(DetectedEntity(
                    text=detected_text,
                    entity_type=entity_type,
                    start=result.start,
                    end=result.end,
                    score=result.score,
                ))
        return entities

    # ------------------------------------------------------------------
    # False-positive filtering (final pass)
    # ------------------------------------------------------------------

    def _filter_false_positives(self, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        """Final filter to catch anything that slipped through."""
        filtered = []
        for entity in entities:
            # Regex-detected entities (structured data) always pass
            if entity.score >= 0.90:
                filtered.append(entity)
                continue

            # Check confidence threshold
            threshold = SCORE_THRESHOLDS.get(entity.entity_type, DEFAULT_SCORE_THRESHOLD)
            if entity.score < threshold:
                continue

            text = entity.text.strip()

            # Minimum length
            if len(text) < 3:
                continue

            # For Italian locale: extra checks
            if self._locale == "it" and entity.entity_type in (
                EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION
            ):
                words = text.split()
                # All words are common vocabulary = false positive
                if all(_is_common_word(w) for w in words):
                    continue
                # Single common word
                if len(words) == 1 and _is_common_word(words[0]):
                    continue
                # Single word that is ALL-CAPS or all-lowercase
                if len(words) == 1:
                    w = words[0]
                    if w.isupper() or w.islower():
                        continue

            filtered.append(entity)

        logger.info(
            f"False-positive filter: {len(entities)} -> {len(filtered)} entities"
        )
        return filtered

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
