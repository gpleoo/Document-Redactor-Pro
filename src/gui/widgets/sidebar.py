"""
Sidebar Widget - Contains all controls: redaction style, regex toggles,
search panel, word list, and action buttons.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame,
    QRadioButton, QButtonGroup, QLineEdit, QCheckBox,
    QPushButton, QHBoxLayout, QGroupBox, QProgressBar,
)

from core.regex_detector import PatternType
from gui.theme import Colors
from gui.widgets.search_panel import SearchPanel
from gui.widgets.word_list_panel import WordListPanel


class Sidebar(QWidget):
    """Main sidebar with all redaction controls."""

    # Signals
    redaction_style_changed = pyqtSignal(str, str)  # (style, custom_text)
    pattern_toggled = pyqtSignal(PatternType, bool)
    scan_requested = pyqtSignal()
    apply_requested = pyqtSignal()
    export_requested = pyqtSignal()
    propagate_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        self._main_layout = QVBoxLayout(content)
        self._main_layout.setContentsMargins(16, 16, 16, 16)
        self._main_layout.setSpacing(16)

        # ── App title ────────────────────────────────────────
        title = QLabel("Document Redactor Pro")
        title.setObjectName("title")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {Colors.ACCENT_HOVER};")
        self._main_layout.addWidget(title)

        subtitle = QLabel("Redazione sicura e 100% offline")
        subtitle.setObjectName("subtitle")
        self._main_layout.addWidget(subtitle)

        self._add_separator()

        # ── Redaction Style ──────────────────────────────────
        self._build_style_section()
        self._add_separator()

        # ── Regex Patterns ───────────────────────────────────
        self._build_patterns_section()
        self._add_separator()

        # ── Search Panel ─────────────────────────────────────
        self.search_panel = SearchPanel()
        self._main_layout.addWidget(self.search_panel)
        self._add_separator()

        # ── Word List + Profiles ─────────────────────────────
        self.word_list_panel = WordListPanel()
        self._main_layout.addWidget(self.word_list_panel)
        self._add_separator()

        # ── Propagation toggle ───────────────────────────────
        self._propagate_check = QCheckBox("Propaga selezione su tutto il documento")
        self._propagate_check.setChecked(True)
        self._propagate_check.setToolTip(
            "Quando selezioni una parola, trova e seleziona automaticamente "
            "tutte le occorrenze identiche nel documento"
        )
        self._propagate_check.toggled.connect(self.propagate_toggled.emit)
        self._main_layout.addWidget(self._propagate_check)

        self._add_separator()

        # ── Action Buttons ───────────────────────────────────
        self._build_actions_section()

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._main_layout.addWidget(self._progress)

        # Status
        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._main_layout.addWidget(self._status_label)

        self._main_layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Build Sections ───────────────────────────────────────
    def _build_style_section(self):
        header = QLabel("Stile Redazione")
        header.setObjectName("sectionHeader")
        self._main_layout.addWidget(header)

        self._style_group = QButtonGroup(self)
        styles = [
            ("black", "Nero (classico)"),
            ("white", "Bianco"),
            ("custom", "Testo sostitutivo"),
        ]

        for value, label in styles:
            rb = QRadioButton(label)
            rb.setProperty("style_value", value)
            self._style_group.addButton(rb)
            self._main_layout.addWidget(rb)
            if value == "black":
                rb.setChecked(True)

        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText("Testo sostitutivo (es. [REDATTO])")
        self._custom_input.setEnabled(False)
        self._main_layout.addWidget(self._custom_input)

        self._style_group.buttonClicked.connect(self._on_style_changed)
        self._custom_input.textChanged.connect(self._on_style_changed)

    def _build_patterns_section(self):
        header = QLabel("Pattern Automatici")
        header.setObjectName("sectionHeader")
        self._main_layout.addWidget(header)

        self._pattern_checks: dict[PatternType, QCheckBox] = {}
        for pt in PatternType:
            cb = QCheckBox(pt.value)
            cb.setChecked(True)
            cb.toggled.connect(lambda checked, p=pt: self.pattern_toggled.emit(p, checked))
            self._pattern_checks[pt] = cb
            self._main_layout.addWidget(cb)

        # Scan button
        scan_row = QHBoxLayout()
        self._scan_btn = QPushButton("Scansiona Pattern")
        self._scan_btn.setObjectName("primary")
        self._scan_btn.clicked.connect(self.scan_requested.emit)
        scan_row.addWidget(self._scan_btn)
        self._main_layout.addLayout(scan_row)

    def _build_actions_section(self):
        header = QLabel("Azioni")
        header.setObjectName("sectionHeader")
        self._main_layout.addWidget(header)

        self._apply_btn = QPushButton("Applica Redazioni")
        self._apply_btn.setObjectName("primary")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self.apply_requested.emit)
        self._main_layout.addWidget(self._apply_btn)

        self._export_btn = QPushButton("Esporta PDF Sanificato")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self.export_requested.emit)
        self._main_layout.addWidget(self._export_btn)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER}; border: none;")
        self._main_layout.addWidget(sep)

    # ── Handlers ─────────────────────────────────────────────
    def _on_style_changed(self, *_):
        btn = self._style_group.checkedButton()
        if not btn:
            return
        style = btn.property("style_value")
        self._custom_input.setEnabled(style == "custom")
        custom_text = self._custom_input.text() if style == "custom" else ""
        self.redaction_style_changed.emit(style, custom_text)

    # ── Public API ─────────────────────────────────────────
    @property
    def propagation_enabled(self) -> bool:
        return self._propagate_check.isChecked()

    def get_enabled_patterns(self) -> set[PatternType]:
        return {pt for pt, cb in self._pattern_checks.items() if cb.isChecked()}

    def get_redaction_style(self) -> tuple[str, str]:
        btn = self._style_group.checkedButton()
        if not btn:
            return ("black", "")
        style = btn.property("style_value")
        custom_text = self._custom_input.text() if style == "custom" else ""
        return (style, custom_text)

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_progress(self, value: int, maximum: int = 100):
        self._progress.setVisible(value < maximum)
        self._progress.setMaximum(maximum)
        self._progress.setValue(value)

    def set_actions_enabled(self, enabled: bool):
        self._apply_btn.setEnabled(enabled)
        self._export_btn.setEnabled(enabled)
