"""
Sidebar Widget - Redaction presets, entity controls, and detection results.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QComboBox, QScrollArea,
    QWidget, QGroupBox, QProgressBar, QSpacerItem, QSizePolicy,
)

from ..core.ner_engine import EntityType


ENTITY_LABELS = {
    EntityType.PERSON: "Names / Persons",
    EntityType.FISCAL_CODE: "Fiscal Codes (IT)",
    EntityType.SSN: "SSN (US)",
    EntityType.IBAN: "IBAN",
    EntityType.EMAIL: "Email Addresses",
    EntityType.PHONE: "Phone Numbers",
    EntityType.ADDRESS: "Addresses",
    EntityType.DATE_OF_BIRTH: "Dates of Birth",
    EntityType.CREDIT_CARD: "Credit Card Numbers",
    EntityType.SIGNATURE: "Signatures",
    EntityType.ORGANIZATION: "Organizations",
    EntityType.LOCATION: "Locations",
}

LOCALE_OPTIONS = [
    ("Italiano", "it"),
    ("English", "en"),
    ("Deutsch", "de"),
    ("Francais", "fr"),
    ("Espanol", "es"),
]


class SidebarWidget(QFrame):
    """Left sidebar with redaction presets and controls."""

    presets_changed = pyqtSignal(set)    # emits set of enabled EntityTypes
    analyze_clicked = pyqtSignal()
    redact_all_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    locale_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(280)
        self._checkboxes: dict[EntityType, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # App title
        title = QLabel("AI Document\nRedactor Pro")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2563eb;")
        layout.addWidget(title)

        subtitle = QLabel("100% Offline Redaction")
        subtitle.setObjectName("statusLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Locale selector
        locale_group = QGroupBox("Language / Locale")
        locale_layout = QVBoxLayout()
        self._locale_combo = QComboBox()
        for label, code in LOCALE_OPTIONS:
            self._locale_combo.addItem(label, code)
        self._locale_combo.currentIndexChanged.connect(self._on_locale_changed)
        locale_layout.addWidget(self._locale_combo)
        locale_group.setLayout(locale_layout)
        layout.addWidget(locale_group)

        # Preset checkboxes
        preset_group = QGroupBox("Redaction Presets")
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(6)

        for entity_type, label in ENTITY_LABELS.items():
            cb = QCheckBox(label)
            cb.setChecked(entity_type in {
                EntityType.PERSON, EntityType.FISCAL_CODE, EntityType.SSN,
                EntityType.IBAN, EntityType.EMAIL, EntityType.PHONE,
                EntityType.CREDIT_CARD,
            })
            cb.stateChanged.connect(self._on_preset_changed)
            self._checkboxes[entity_type] = cb
            preset_layout.addWidget(cb)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Select / Deselect all
        sel_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.setObjectName("secondaryButton")
        select_all.clicked.connect(self._select_all)
        deselect_all = QPushButton("Deselect All")
        deselect_all.setObjectName("secondaryButton")
        deselect_all.clicked.connect(self._deselect_all)
        sel_layout.addWidget(select_all)
        sel_layout.addWidget(deselect_all)
        layout.addLayout(sel_layout)

        layout.addSpacing(8)

        # Analysis progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addSpacing(4)

        # Detection results summary
        self._results_group = QGroupBox("Detection Results")
        self._results_layout = QVBoxLayout()
        self._results_label = QLabel("No analysis performed yet.")
        self._results_label.setWordWrap(True)
        self._results_label.setObjectName("statusLabel")
        self._results_layout.addWidget(self._results_label)
        self._results_group.setLayout(self._results_layout)
        self._results_group.setVisible(False)
        layout.addWidget(self._results_group)

        layout.addSpacing(8)

        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self._analyze_btn = QPushButton("Analyze Document")
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.clicked.connect(self.analyze_clicked.emit)
        actions_layout.addWidget(self._analyze_btn)

        self._redact_btn = QPushButton("Redact All Detected")
        self._redact_btn.setEnabled(False)
        self._redact_btn.clicked.connect(self.redact_all_clicked.emit)
        actions_layout.addWidget(self._redact_btn)

        self._clear_btn = QPushButton("Clear Redactions")
        self._clear_btn.setObjectName("secondaryButton")
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self.clear_clicked.emit)
        actions_layout.addWidget(self._clear_btn)

        actions_layout.addSpacing(4)

        self._export_btn = QPushButton("Export Sanitized Document")
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet(
            "QPushButton { background-color: #22c55e; font-size: 14px; padding: 12px; }"
            "QPushButton:hover { background-color: #16a34a; }"
        )
        self._export_btn.clicked.connect(self.export_clicked.emit)
        actions_layout.addWidget(self._export_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Footer
        footer = QLabel("v1.0.0 | Privacy-First")
        footer.setObjectName("statusLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def get_enabled_entities(self) -> set[EntityType]:
        return {et for et, cb in self._checkboxes.items() if cb.isChecked()}

    def set_document_loaded(self, loaded: bool):
        self._analyze_btn.setEnabled(loaded)
        if not loaded:
            self._redact_btn.setEnabled(False)
            self._clear_btn.setEnabled(False)
            self._export_btn.setEnabled(False)
            self._results_group.setVisible(False)

    def set_analysis_complete(self, entity_counts: dict[EntityType, int]):
        self._redact_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._results_group.setVisible(True)

        lines = []
        total = 0
        for et, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
            label = ENTITY_LABELS.get(et, et.value)
            lines.append(f"  {label}: {count}")
            total += count
        summary = f"Found {total} sensitive items:\n" + "\n".join(lines)
        self._results_label.setText(summary)

    def set_progress(self, value: int, status: str = ""):
        self._progress_bar.setVisible(value < 100)
        self._progress_bar.setValue(value)
        if status:
            self._status_label.setText(status)

    def _on_preset_changed(self):
        self.presets_changed.emit(self.get_enabled_entities())

    def _on_locale_changed(self):
        code = self._locale_combo.currentData()
        self.locale_changed.emit(code)

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)
