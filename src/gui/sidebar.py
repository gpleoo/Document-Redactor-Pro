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

from core.ner_engine import EntityType
from utils.i18n import I18n


ENTITY_I18N_KEYS = {
    EntityType.PERSON: "entity.person",
    EntityType.FISCAL_CODE: "entity.fiscal_code",
    EntityType.SSN: "entity.ssn",
    EntityType.IBAN: "entity.iban",
    EntityType.EMAIL: "entity.email",
    EntityType.PHONE: "entity.phone",
    EntityType.ADDRESS: "entity.address",
    EntityType.DATE_OF_BIRTH: "entity.dob",
    EntityType.CREDIT_CARD: "entity.credit_card",
    EntityType.SIGNATURE: "entity.signature",
    EntityType.ORGANIZATION: "entity.organization",
    EntityType.LOCATION: "entity.location",
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

    presets_changed = pyqtSignal(set)
    analyze_clicked = pyqtSignal()
    redact_all_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    locale_changed = pyqtSignal(str)

    def __init__(self, i18n: I18n, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(280)
        self._i18n = i18n
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

        self._subtitle = QLabel(self._i18n.t("app.subtitle"))
        self._subtitle.setObjectName("statusLabel")
        layout.addWidget(self._subtitle)

        layout.addSpacing(8)

        # Locale selector
        self._locale_group = QGroupBox(self._i18n.t("sidebar.locale"))
        locale_layout = QVBoxLayout()
        self._locale_combo = QComboBox()
        for label, code in LOCALE_OPTIONS:
            self._locale_combo.addItem(label, code)
        self._locale_combo.currentIndexChanged.connect(self._on_locale_changed)
        locale_layout.addWidget(self._locale_combo)
        self._locale_group.setLayout(locale_layout)
        layout.addWidget(self._locale_group)

        # Preset checkboxes
        self._preset_group = QGroupBox(self._i18n.t("sidebar.presets"))
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(6)

        for entity_type, i18n_key in ENTITY_I18N_KEYS.items():
            cb = QCheckBox(self._i18n.t(i18n_key))
            cb.setChecked(entity_type in {
                EntityType.PERSON, EntityType.FISCAL_CODE, EntityType.SSN,
                EntityType.IBAN, EntityType.EMAIL, EntityType.PHONE,
                EntityType.CREDIT_CARD,
            })
            cb.stateChanged.connect(self._on_preset_changed)
            self._checkboxes[entity_type] = cb
            preset_layout.addWidget(cb)

        self._preset_group.setLayout(preset_layout)
        layout.addWidget(self._preset_group)

        # Select / Deselect all
        sel_layout = QHBoxLayout()
        self._select_all_btn = QPushButton(self._i18n.t("action.select_all"))
        self._select_all_btn.setObjectName("secondaryButton")
        self._select_all_btn.clicked.connect(self._select_all)
        self._deselect_all_btn = QPushButton(self._i18n.t("action.deselect_all"))
        self._deselect_all_btn.setObjectName("secondaryButton")
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        sel_layout.addWidget(self._select_all_btn)
        sel_layout.addWidget(self._deselect_all_btn)
        layout.addLayout(sel_layout)

        layout.addSpacing(8)

        # Analysis progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel(self._i18n.t("status.ready"))
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addSpacing(4)

        # Detection results summary
        self._results_group = QGroupBox(self._i18n.t("sidebar.results"))
        self._results_layout = QVBoxLayout()
        self._results_label = QLabel("")
        self._results_label.setWordWrap(True)
        self._results_label.setObjectName("statusLabel")
        self._results_layout.addWidget(self._results_label)
        self._results_group.setLayout(self._results_layout)
        self._results_group.setVisible(False)
        layout.addWidget(self._results_group)

        layout.addSpacing(8)

        # Action buttons
        self._actions_group = QGroupBox(self._i18n.t("sidebar.actions"))
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self._analyze_btn = QPushButton(self._i18n.t("action.analyze"))
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.clicked.connect(self.analyze_clicked.emit)
        actions_layout.addWidget(self._analyze_btn)

        self._redact_btn = QPushButton(self._i18n.t("action.redact_all"))
        self._redact_btn.setEnabled(False)
        self._redact_btn.clicked.connect(self.redact_all_clicked.emit)
        actions_layout.addWidget(self._redact_btn)

        self._clear_btn = QPushButton(self._i18n.t("action.clear"))
        self._clear_btn.setObjectName("secondaryButton")
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self.clear_clicked.emit)
        actions_layout.addWidget(self._clear_btn)

        actions_layout.addSpacing(4)

        self._export_btn = QPushButton(self._i18n.t("action.export"))
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet(
            "QPushButton { background-color: #22c55e; font-size: 14px; padding: 12px; }"
            "QPushButton:hover { background-color: #16a34a; }"
        )
        self._export_btn.clicked.connect(self.export_clicked.emit)
        actions_layout.addWidget(self._export_btn)

        self._actions_group.setLayout(actions_layout)
        layout.addWidget(self._actions_group)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Footer
        self._footer = QLabel(self._i18n.t("footer.version"))
        self._footer.setObjectName("statusLabel")
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._footer)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def update_labels(self):
        """Refresh all UI labels after locale change."""
        t = self._i18n.t
        self._subtitle.setText(t("app.subtitle"))
        self._locale_group.setTitle(t("sidebar.locale"))
        self._preset_group.setTitle(t("sidebar.presets"))
        self._results_group.setTitle(t("sidebar.results"))
        self._actions_group.setTitle(t("sidebar.actions"))
        self._analyze_btn.setText(t("action.analyze"))
        self._redact_btn.setText(t("action.redact_all"))
        self._clear_btn.setText(t("action.clear"))
        self._export_btn.setText(t("action.export"))
        self._select_all_btn.setText(t("action.select_all"))
        self._deselect_all_btn.setText(t("action.deselect_all"))
        self._status_label.setText(t("status.ready"))
        self._footer.setText(t("footer.version"))

        for entity_type, i18n_key in ENTITY_I18N_KEYS.items():
            if entity_type in self._checkboxes:
                self._checkboxes[entity_type].setText(t(i18n_key))

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

        t = self._i18n.t
        lines = []
        total = 0
        for et, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
            i18n_key = ENTITY_I18N_KEYS.get(et, et.value)
            label = t(i18n_key)
            lines.append(f"  {label}: {count}")
            total += count
        summary = t("status.complete", count=total) + "\n" + "\n".join(lines)
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
        if code:
            self.locale_changed.emit(code)

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)
