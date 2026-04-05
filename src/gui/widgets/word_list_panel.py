"""
Word List Panel - Manages the list of words to redact + profile load/save.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QInputDialog, QMessageBox, QFrame,
)

from gui.theme import Colors


class WordListPanel(QWidget):
    """Panel showing words queued for redaction, with profile management."""

    words_changed = pyqtSignal(list)        # Updated word list
    profile_load_requested = pyqtSignal(str)  # Profile name
    profile_save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._words: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section header
        header = QLabel("Parole da Oscurare")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        # Manual add row
        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self._word_input = QLineEdit()
        self._word_input.setPlaceholderText("Aggiungi parola manualmente...")
        self._word_input.returnPressed.connect(self._on_manual_add)

        self._add_btn = QPushButton("+")
        self._add_btn.setObjectName("primary")
        self._add_btn.setFixedSize(36, 36)
        self._add_btn.setToolTip("Aggiungi parola")
        self._add_btn.clicked.connect(self._on_manual_add)

        add_row.addWidget(self._word_input, 1)
        add_row.addWidget(self._add_btn)
        layout.addLayout(add_row)

        # Word list
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self._list, 1)

        # Word count
        self._count_label = QLabel("0 parole")
        self._count_label.setObjectName("statusLabel")
        layout.addWidget(self._count_label)

        # Remove / Clear buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._remove_btn = QPushButton("Rimuovi Selezionate")
        self._remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self._remove_btn)

        self._clear_btn = QPushButton("Svuota Lista")
        self._clear_btn.setObjectName("danger")
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._clear_btn)

        layout.addLayout(btn_row)

        # ── Profile section ──────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {Colors.BORDER};")
        layout.addWidget(sep)

        profile_header = QLabel("Profili di Redazione")
        profile_header.setObjectName("sectionHeader")
        layout.addWidget(profile_header)

        # Profile selector
        self._profile_combo = QComboBox()
        self._profile_combo.setPlaceholderText("Seleziona profilo...")
        layout.addWidget(self._profile_combo)

        profile_btns = QHBoxLayout()
        profile_btns.setSpacing(6)

        self._load_btn = QPushButton("Carica")
        self._load_btn.setObjectName("primary")
        self._load_btn.clicked.connect(self._on_load_profile)
        profile_btns.addWidget(self._load_btn)

        self._save_btn = QPushButton("Salva")
        self._save_btn.clicked.connect(self._on_save_profile)
        profile_btns.addWidget(self._save_btn)

        self._delete_btn = QPushButton("Elimina")
        self._delete_btn.setObjectName("danger")
        self._delete_btn.clicked.connect(self._on_delete_profile)
        profile_btns.addWidget(self._delete_btn)

        layout.addLayout(profile_btns)

    # ── Public API ─────────────────────────────────────────
    def add_word(self, word: str) -> bool:
        w = word.strip()
        if w and w not in self._words:
            self._words.append(w)
            self._refresh_list()
            self.words_changed.emit(self._words.copy())
            return True
        return False

    def add_words(self, words: list[str]):
        changed = False
        for w in words:
            w = w.strip()
            if w and w not in self._words:
                self._words.append(w)
                changed = True
        if changed:
            self._refresh_list()
            self.words_changed.emit(self._words.copy())

    def get_words(self) -> list[str]:
        return self._words.copy()

    def set_words(self, words: list[str]):
        self._words = list(words)
        self._refresh_list()
        self.words_changed.emit(self._words.copy())

    def set_profile_list(self, names: list[str]):
        self._profile_combo.clear()
        for name in names:
            self._profile_combo.addItem(name)

    # ── Private ────────────────────────────────────────────
    def _refresh_list(self):
        self._list.clear()
        for w in self._words:
            item = QListWidgetItem(w)
            self._list.addItem(item)
        n = len(self._words)
        self._count_label.setText(f"{n} parol{'a' if n == 1 else 'e'}")

    def _on_manual_add(self):
        text = self._word_input.text().strip()
        if text:
            self.add_word(text)
            self._word_input.clear()

    def _on_remove(self):
        selected = self._list.selectedItems()
        for item in selected:
            word = item.text()
            if word in self._words:
                self._words.remove(word)
        self._refresh_list()
        self.words_changed.emit(self._words.copy())

    def _on_clear(self):
        if not self._words:
            return
        reply = QMessageBox.question(
            self, "Conferma", "Svuotare la lista di parole?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._words.clear()
            self._refresh_list()
            self.words_changed.emit(self._words.copy())

    def _on_load_profile(self):
        name = self._profile_combo.currentText()
        if name:
            self.profile_load_requested.emit(name)

    def _on_save_profile(self):
        self.profile_save_requested.emit()

    def _on_delete_profile(self):
        name = self._profile_combo.currentText()
        if not name:
            return
        reply = QMessageBox.question(
            self, "Conferma", f"Eliminare il profilo \"{name}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Will be handled by main window
            self.profile_load_requested.emit(f"__DELETE__{name}")
