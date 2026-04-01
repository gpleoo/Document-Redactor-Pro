"""
Search Panel - Live search bar with results for finding words across all pages.
Core of the manual redaction workflow.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QFrame,
)

from gui.theme import Colors


class SearchPanel(QWidget):
    """Search bar + results list. User types a word, sees all matches."""

    word_add_requested = pyqtSignal(str)        # Add word to redaction list
    result_clicked = pyqtSignal(int, int)       # (page, block_index)
    search_changed = pyqtSignal(str)            # Live search text changed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []  # list of SearchResult
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section header
        header = QLabel("Cerca nel Documento")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("searchBar")
        self._search_input.setPlaceholderText("Cerca parola o frase...")
        self._search_input.setClearButtonEnabled(True)

        self._add_btn = QPushButton("+ Aggiungi")
        self._add_btn.setObjectName("primary")
        self._add_btn.setFixedHeight(40)
        self._add_btn.setEnabled(False)
        self._add_btn.setToolTip("Aggiungi questa parola alla lista di redazione")
        self._add_btn.clicked.connect(self._on_add_clicked)

        search_row.addWidget(self._search_input, 1)
        search_row.addWidget(self._add_btn)
        layout.addLayout(search_row)

        # Options row
        opts = QHBoxLayout()
        opts.setSpacing(12)
        self._case_check = QCheckBox("Maiuscole/Minuscole")
        self._case_check.setToolTip("Ricerca sensibile a maiuscole/minuscole")
        opts.addWidget(self._case_check)

        self._count_label = QLabel("")
        self._count_label.setObjectName("statusLabel")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        opts.addWidget(self._count_label, 1)
        layout.addLayout(opts)

        # Results list
        self._result_list = QListWidget()
        self._result_list.setMaximumHeight(200)
        self._result_list.itemClicked.connect(self._on_result_clicked)
        layout.addWidget(self._result_list)

        # Debounce timer for live search
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._emit_search)

        self._search_input.textChanged.connect(self._on_text_changed)
        self._case_check.toggled.connect(lambda: self._emit_search())

    def _on_text_changed(self, text: str):
        self._add_btn.setEnabled(bool(text.strip()))
        self._debounce.start()

    def _emit_search(self):
        self.search_changed.emit(self._search_input.text())

    def _on_add_clicked(self):
        text = self._search_input.text().strip()
        if text:
            self.word_add_requested.emit(text)

    def _on_result_clicked(self, item: QListWidgetItem):
        idx = self._result_list.row(item)
        if 0 <= idx < len(self._results):
            r = self._results[idx]
            self.result_clicked.emit(r.page, r.block_index)

    # ── Public API ─────────────────────────────────────────
    @property
    def case_sensitive(self) -> bool:
        return self._case_check.isChecked()

    @property
    def search_text(self) -> str:
        return self._search_input.text().strip()

    def set_results(self, results: list):
        """Update the results list. Each result has .page, .text, .block_index."""
        self._results = results
        self._result_list.clear()
        for r in results:
            item = QListWidgetItem(f"Pag. {r.page + 1}:  \"{r.text}\"")
            self._result_list.addItem(item)
        count = len(results)
        self._count_label.setText(f"{count} risultat{'o' if count == 1 else 'i'}" if count else "")

    def clear_results(self):
        self._results = []
        self._result_list.clear()
        self._count_label.setText("")
