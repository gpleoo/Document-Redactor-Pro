"""
Main Window - Integrates all widgets into the Document Redactor Pro application.
Coordinates document loading, search, redaction, and export workflows.
"""

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFileDialog, QMessageBox, QInputDialog,
    QApplication,
)

import fitz

from core.ocr_engine import OCREngine, TextBlock, PageData
from core.regex_detector import RegexDetector, PatternType
from core.text_search import TextSearchEngine
from core.pdf_processor import PDFProcessor
from core.file_manager import FileManager
from core.profile_manager import ProfileManager, RedactionProfile

from gui.theme import Colors
from gui.widgets.drop_zone import DropZone
from gui.widgets.preview_widget import PreviewWidget, RENDER_SCALE
from gui.widgets.sidebar import Sidebar

logger = logging.getLogger(__name__)


class ExtractWorker(QThread):
    """Background thread for text extraction."""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)  # list[PageData]
    error = pyqtSignal(str)

    def __init__(self, ocr: OCREngine, path: str, is_pdf: bool):
        super().__init__()
        self._ocr = ocr
        self._path = path
        self._is_pdf = is_pdf

    def run(self):
        try:
            if self._is_pdf:
                pages = self._ocr.extract_from_pdf(self._path, self.progress.emit)
            else:
                page = self._ocr.extract_from_image(self._path)
                pages = [page]
            self.finished.emit(pages)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Redactor Pro")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Core engines
        self._ocr = OCREngine()
        self._detector = RegexDetector()
        self._search_engine = TextSearchEngine()
        self._pdf_proc = PDFProcessor()
        self._file_mgr = FileManager()
        self._profile_mgr = ProfileManager()

        # State
        self._pages_data: list[PageData] = []
        self._selected_global_indices: set[int] = set()  # global block indices to redact
        self._worker: ExtractWorker | None = None

        self._setup_ui()
        self._connect_signals()
        self._refresh_profiles()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # Content area (stacked: drop zone vs preview)
        self._stack = QStackedWidget()

        # Page 0: Drop zone
        self._drop_zone = DropZone()
        self._stack.addWidget(self._drop_zone)

        # Page 1: Preview
        self._preview = PreviewWidget()
        self._stack.addWidget(self._preview)

        self._stack.setCurrentIndex(0)
        main_layout.addWidget(self._stack, 1)

    def _connect_signals(self):
        # File loading
        self._drop_zone.file_dropped.connect(self._load_document)

        # Preview click
        self._preview.block_clicked.connect(self._on_block_clicked)

        # Search
        self._sidebar.search_panel.search_changed.connect(self._on_search)
        self._sidebar.search_panel.word_add_requested.connect(self._on_word_add_from_search)
        self._sidebar.search_panel.result_clicked.connect(self._on_search_result_clicked)

        # Word list
        self._sidebar.word_list_panel.words_changed.connect(self._on_words_changed)
        self._sidebar.word_list_panel.profile_load_requested.connect(self._on_profile_action)
        self._sidebar.word_list_panel.profile_save_requested.connect(self._on_save_profile)

        # Redaction style
        self._sidebar.redaction_style_changed.connect(self._on_style_changed)

        # Pattern scan
        self._sidebar.scan_requested.connect(self._on_scan_patterns)

        # Actions
        self._sidebar.apply_requested.connect(self._on_apply_redactions)
        self._sidebar.export_requested.connect(self._on_export)

    # ═══════════════════════════════════════════════════════
    # DOCUMENT LOADING
    # ═══════════════════════════════════════════════════════
    def _load_document(self, file_path: str):
        if not self._file_mgr.is_supported(file_path):
            QMessageBox.warning(self, "Errore", "Formato file non supportato.")
            return

        working = self._file_mgr.load_file(file_path)
        if not working:
            QMessageBox.warning(self, "Errore", "Impossibile caricare il file.")
            return

        # Load into PDF processor
        if self._file_mgr.is_pdf:
            ok = self._pdf_proc.load(working)
        else:
            ok = self._pdf_proc.load_image(working)

        if not ok:
            QMessageBox.warning(self, "Errore", "Impossibile elaborare il file.")
            return

        self._sidebar.set_status(f"Caricamento: {Path(file_path).name}")
        self._sidebar.set_progress(0, 100)

        # Reset state
        self._pages_data = []
        self._selected_global_indices.clear()
        self._preview.clear_pages()

        # Start extraction in background
        self._worker = ExtractWorker(self._ocr, working, self._file_mgr.is_pdf)
        self._worker.progress.connect(self._on_extract_progress)
        self._worker.finished.connect(self._on_extract_done)
        self._worker.error.connect(self._on_extract_error)
        self._worker.start()

    def _on_extract_progress(self, current: int, total: int):
        self._sidebar.set_progress(current, total)
        self._sidebar.set_status(f"Estrazione testo: pagina {current}/{total}")

    def _on_extract_done(self, pages: list):
        self._pages_data = pages
        self._sidebar.set_progress(100, 100)

        # Index blocks for search
        all_blocks = [p.blocks for p in pages]
        self._search_engine.set_blocks(all_blocks)

        # Render pages
        self._render_all_pages()

        self._stack.setCurrentIndex(1)
        self._sidebar.set_actions_enabled(True)

        total_words = sum(len(p.blocks) for p in pages)
        self._sidebar.set_status(
            f"{len(pages)} pagine, {total_words} parole estratte"
        )
        self._worker = None

    def _on_extract_error(self, msg: str):
        QMessageBox.critical(self, "Errore Estrazione", msg)
        self._sidebar.set_status("Errore durante l'estrazione")
        self._sidebar.set_progress(100, 100)
        self._worker = None

    def _render_all_pages(self):
        self._preview.clear_pages()
        for page_data in self._pages_data:
            pix = self._pdf_proc.get_page_pixmap(page_data.page_number, zoom=RENDER_SCALE)
            if pix:
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                qpix = QPixmap.fromImage(img)
                self._preview.add_page(qpix, page_data.blocks, page_data.page_number)

    # ═══════════════════════════════════════════════════════
    # BLOCK SELECTION & PROPAGATION
    # ═══════════════════════════════════════════════════════
    def _on_block_clicked(self, page_idx: int, block_idx_in_page: int):
        """Handle click on a block in the preview."""
        if page_idx >= len(self._pages_data):
            return

        page_data = self._pages_data[page_idx]
        if block_idx_in_page >= len(page_data.blocks):
            return

        block = page_data.blocks[block_idx_in_page]
        start, _ = self._search_engine.get_page_range(page_idx)
        global_idx = start + block_idx_in_page

        # Toggle selection
        if global_idx in self._selected_global_indices:
            # Deselect this block (and propagated ones if propagation is on)
            if self._sidebar.propagation_enabled:
                propagated = self._search_engine.search_exact_word(block.text)
                for gi in propagated:
                    self._selected_global_indices.discard(gi)
            else:
                self._selected_global_indices.discard(global_idx)
        else:
            # Select this block (and propagate if enabled)
            if self._sidebar.propagation_enabled:
                propagated = self._search_engine.search_exact_word(block.text)
                self._selected_global_indices.update(propagated)
                # Also add to word list
                self._sidebar.word_list_panel.add_word(block.text)
            else:
                self._selected_global_indices.add(global_idx)

        self._update_preview_selections()

    def _update_preview_selections(self):
        """Update all page canvases with current selection state."""
        selections: dict[int, set[int]] = {}
        for page_data in self._pages_data:
            pidx = page_data.page_number
            start, end = self._search_engine.get_page_range(pidx)
            page_selected = set()
            for gi in range(start, end):
                if gi in self._selected_global_indices:
                    page_selected.add(gi - start)
            if page_selected:
                selections[pidx] = page_selected
        self._preview.set_all_selections(selections)

    # ═══════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════
    def _on_search(self, query: str):
        if not query.strip():
            self._sidebar.search_panel.clear_results()
            return
        results = self._search_engine.search(
            query, case_sensitive=self._sidebar.search_panel.case_sensitive
        )
        self._sidebar.search_panel.set_results(results)

    def _on_word_add_from_search(self, word: str):
        self._sidebar.word_list_panel.add_word(word)

    def _on_search_result_clicked(self, page: int, block_index: int):
        self._preview.scroll_to_page(page)

    # ═══════════════════════════════════════════════════════
    # WORD LIST → SELECTION SYNC
    # ═══════════════════════════════════════════════════════
    def _on_words_changed(self, words: list[str]):
        """Rebuild selection from current word list."""
        self._selected_global_indices.clear()
        if words:
            indices = self._search_engine.search_multi_words(words)
            self._selected_global_indices = indices
        self._update_preview_selections()

    # ═══════════════════════════════════════════════════════
    # PATTERN SCANNING
    # ═══════════════════════════════════════════════════════
    def _on_scan_patterns(self):
        if not self._pages_data:
            return

        enabled = self._sidebar.get_enabled_patterns()
        self._detector.enabled_types = enabled

        found_words: set[str] = set()
        for page_data in self._pages_data:
            matched = self._detector.scan_blocks(page_data.blocks)
            for block_idx, matches in matched.items():
                found_words.add(page_data.blocks[block_idx].text)

        if found_words:
            self._sidebar.word_list_panel.add_words(list(found_words))
            self._sidebar.set_status(f"Pattern trovati: {len(found_words)} parole aggiunte")
        else:
            self._sidebar.set_status("Nessun pattern trovato")

    # ═══════════════════════════════════════════════════════
    # REDACTION STYLE
    # ═══════════════════════════════════════════════════════
    def _on_style_changed(self, style: str, custom_text: str):
        self._preview.set_redaction_style(style, custom_text)

    # ═══════════════════════════════════════════════════════
    # PROFILES
    # ═══════════════════════════════════════════════════════
    def _refresh_profiles(self):
        names = self._profile_mgr.list_profiles()
        self._sidebar.word_list_panel.set_profile_list(names)

    def _on_profile_action(self, name: str):
        if name.startswith("__DELETE__"):
            real_name = name[10:]
            self._profile_mgr.delete_profile(real_name)
            self._refresh_profiles()
            self._sidebar.set_status(f"Profilo \"{real_name}\" eliminato")
            return

        profile = self._profile_mgr.load_profile(name)
        if profile:
            self._sidebar.word_list_panel.set_words(profile.words)
            self._sidebar.set_status(f"Profilo \"{profile.name}\" caricato ({len(profile.words)} parole)")
        else:
            QMessageBox.warning(self, "Errore", f"Impossibile caricare il profilo \"{name}\"")

    def _on_save_profile(self):
        words = self._sidebar.word_list_panel.get_words()
        if not words:
            QMessageBox.information(self, "Info", "La lista parole è vuota.")
            return

        name, ok = QInputDialog.getText(
            self, "Salva Profilo", "Nome del profilo:",
        )
        if ok and name.strip():
            style, custom_text = self._sidebar.get_redaction_style()
            profile = RedactionProfile(
                name=name.strip(),
                words=words,
                redaction_style=style,
                custom_text=custom_text,
            )
            if self._profile_mgr.save_profile(profile):
                self._refresh_profiles()
                self._sidebar.set_status(f"Profilo \"{name}\" salvato")
            else:
                QMessageBox.warning(self, "Errore", "Impossibile salvare il profilo.")

    # ═══════════════════════════════════════════════════════
    # APPLY & EXPORT
    # ═══════════════════════════════════════════════════════
    def _on_apply_redactions(self):
        if not self._selected_global_indices:
            QMessageBox.information(self, "Info", "Nessuna parola selezionata per la redazione.")
            return

        reply = QMessageBox.question(
            self, "Conferma Redazione",
            f"Applicare la redazione a {len(self._selected_global_indices)} elementi?\n"
            "Questa operazione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._sidebar.set_status("Applicazione redazioni...")

        # Collect blocks to redact
        blocks_to_redact: list[TextBlock] = []
        for gi in self._selected_global_indices:
            block = self._search_engine.get_block(gi)
            if block:
                blocks_to_redact.append(block)

        # Get redaction style
        style, custom_text = self._sidebar.get_redaction_style()
        fill = (0, 0, 0) if style == "black" else (1, 1, 1)
        text_color = (1, 1, 1) if style == "black" else (0, 0, 0)
        replacement = custom_text if style == "custom" else ""

        areas = self._pdf_proc.blocks_to_areas(
            blocks_to_redact, fill_color=fill,
            text_color=text_color, replacement_text=replacement,
        )

        ok = self._pdf_proc.apply_redactions(
            areas, progress_cb=lambda c, t: self._sidebar.set_progress(c, t)
        )
        if ok:
            self._pdf_proc.flatten()
            self._sidebar.set_status(
                f"Redazione applicata: {len(blocks_to_redact)} elementi oscurati"
            )
            # Re-render to show redacted PDF
            self._render_all_pages()
            self._selected_global_indices.clear()
            self._update_preview_selections()
        else:
            QMessageBox.critical(self, "Errore", "Errore durante l'applicazione delle redazioni.")
            self._sidebar.set_status("Errore redazione")

    def _on_export(self):
        if not self._pdf_proc.is_loaded:
            return

        default_path = self._file_mgr.get_export_path()
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta PDF Sanificato", default_path,
            "PDF (*.pdf)",
        )
        if path:
            if self._pdf_proc.export(path):
                self._sidebar.set_status(f"Esportato: {Path(path).name}")
                QMessageBox.information(
                    self, "Esportazione Completata",
                    f"Il documento sanificato è stato salvato in:\n{path}",
                )
            else:
                QMessageBox.critical(self, "Errore", "Errore durante l'esportazione.")

    # ═══════════════════════════════════════════════════════
    # CLEANUP
    # ═══════════════════════════════════════════════════════
    def closeEvent(self, event):
        self._pdf_proc.close()
        self._file_mgr.cleanup()
        super().closeEvent(event)
