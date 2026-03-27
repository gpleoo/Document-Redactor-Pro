"""
Main Window - Primary application window integrating all components.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap, QAction, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QMessageBox, QSplitter, QApplication, QStackedWidget,
)

from core.ocr_engine import OCREngine, TextBlock, PageData
from core.ner_engine import NEREngine, EntityType, DetectedEntity
from core.pdf_processor import PDFProcessor, RedactionArea
from core.file_manager import FileManager
from gui.theme import DarkTheme
from gui.drop_zone import DropZoneWidget
from gui.preview_widget import PreviewWidget
from gui.sidebar import SidebarWidget

logger = logging.getLogger(__name__)


class AnalysisWorker(QObject):
    """Background worker for OCR + NER analysis."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list, list)  # pages, entities
    error = pyqtSignal(str)

    def __init__(self, ocr: OCREngine, ner: NEREngine, file_path: str, is_pdf: bool):
        super().__init__()
        self._ocr = ocr
        self._ner = ner
        self._file_path = file_path
        self._is_pdf = is_pdf

    def run(self):
        try:
            self.progress.emit(10, "Running OCR extraction...")

            if self._is_pdf:
                def ocr_progress(current, total):
                    pct = int(10 + (current / max(total, 1)) * 40)
                    self.progress.emit(pct, f"OCR: page {current}/{total}")
                pages = self._ocr.extract_from_pdf(self._file_path, ocr_progress)
            else:
                pages = [self._ocr.extract_from_image(self._file_path)]
                self.progress.emit(50, "OCR complete")

            self.progress.emit(60, "Running NER analysis...")

            all_entities: list[DetectedEntity] = []
            total_pages = len(pages)
            for i, page_data in enumerate(pages):
                if page_data.blocks:
                    entities = self._ner.analyze_blocks(page_data.blocks)
                    all_entities.extend(entities)
                pct = int(60 + ((i + 1) / max(total_pages, 1)) * 35)
                self.progress.emit(pct, f"NER: page {i + 1}/{total_pages}")

            self.progress.emit(100, f"Analysis complete: {len(all_entities)} entities found")
            self.finished.emit(pages, all_entities)

        except Exception as e:
            logger.exception("Analysis failed")
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Primary application window."""

    APP_TITLE = "AI Document Redactor Pro"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.APP_TITLE)
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Core engines
        self._file_manager = FileManager()
        self._ocr_engine = OCREngine()
        self._ner_engine = NEREngine()
        self._pdf_processor = PDFProcessor()

        # State
        self._pages: list[PageData] = []
        self._entities: list[DetectedEntity] = []
        self._current_page_idx = 0
        self._redacted_block_indices: set[int] = set()
        self._ai_detected_indices: set[int] = set()
        self._all_blocks: list[TextBlock] = []
        self._page_block_offsets: list[tuple[int, int]] = []  # (start_idx, end_idx) per page

        self._analysis_thread: Optional[QThread] = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = SidebarWidget()
        self._sidebar.analyze_clicked.connect(self._on_analyze)
        self._sidebar.redact_all_clicked.connect(self._on_redact_all_detected)
        self._sidebar.clear_clicked.connect(self._on_clear_redactions)
        self._sidebar.export_clicked.connect(self._on_export)
        self._sidebar.locale_changed.connect(self._on_locale_changed)
        self._sidebar.presets_changed.connect(self._on_presets_changed)

        # Content area (stacked: drop zone vs preview)
        self._content_stack = QStackedWidget()

        # Drop zone (index 0)
        self._drop_zone = DropZoneWidget()
        self._drop_zone.file_dropped.connect(self._on_file_loaded)
        self._content_stack.addWidget(self._drop_zone)

        # Preview (index 1)
        self._preview = PreviewWidget()
        self._preview.block_toggled.connect(self._on_block_toggled)
        self._preview.prev_button.clicked.connect(self._on_prev_page)
        self._preview.next_button.clicked.connect(self._on_next_page)
        self._content_stack.addWidget(self._preview)

        self._content_stack.setCurrentIndex(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._content_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 1120])

        main_layout.addWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        export_action = QAction("&Export Redacted...", self)
        export_action.setShortcut("Ctrl+Shift+S")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit")

        analyze_action = QAction("&Analyze Document", self)
        analyze_action.setShortcut("Ctrl+A")
        analyze_action.triggered.connect(self._on_analyze)
        edit_menu.addAction(analyze_action)

        redact_all_action = QAction("&Redact All Detected", self)
        redact_all_action.setShortcut("Ctrl+R")
        redact_all_action.triggered.connect(self._on_redact_all_detected)
        edit_menu.addAction(redact_all_action)

        clear_action = QAction("&Clear Redactions", self)
        clear_action.triggered.connect(self._on_clear_redactions)
        edit_menu.addAction(clear_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # --- File Operations ---

    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "Supported Files (*.pdf *.jpg *.jpeg *.png);;PDF Files (*.pdf);;Images (*.jpg *.jpeg *.png)"
        )
        if path:
            self._on_file_loaded(path)

    def _on_file_loaded(self, file_path: str):
        self._reset_state()

        working = self._file_manager.load_file(file_path)
        if not working:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{file_path}")
            return

        if self._file_manager.is_pdf:
            success = self._pdf_processor.load(working)
        else:
            success = self._pdf_processor.load_image(working)

        if not success:
            QMessageBox.critical(self, "Error", "Failed to process the document.")
            return

        self.setWindowTitle(f"{self.APP_TITLE} - {os.path.basename(file_path)}")
        self._sidebar.set_document_loaded(True)
        self._sidebar.set_progress(0, "Document loaded. Click 'Analyze' to start.")
        self._content_stack.setCurrentIndex(1)

        self._render_page(0)

    def _render_page(self, page_idx: int):
        if not self._pdf_processor.is_loaded:
            return
        if page_idx < 0 or page_idx >= self._pdf_processor.page_count:
            return

        self._current_page_idx = page_idx
        pix = self._pdf_processor.get_page_pixmap(page_idx, zoom=1.5)
        if not pix:
            return

        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)

        page_blocks = self._get_page_blocks(page_idx)

        self._preview.display_page(
            pixmap, page_blocks,
            page_idx, self._pdf_processor.page_count,
        )
        self._update_preview_overlays()

    def _get_page_blocks(self, page_idx: int) -> list[TextBlock]:
        if page_idx < len(self._pages):
            return self._pages[page_idx].blocks
        return []

    def _get_global_block_offset(self, page_idx: int) -> int:
        if page_idx < len(self._page_block_offsets):
            return self._page_block_offsets[page_idx][0]
        return 0

    def _update_preview_overlays(self):
        offset = self._get_global_block_offset(self._current_page_idx)
        page_blocks = self._get_page_blocks(self._current_page_idx)
        num_blocks = len(page_blocks)

        local_redacted = {i for i in range(num_blocks) if (i + offset) in self._redacted_block_indices}
        local_detected = {i for i in range(num_blocks) if (i + offset) in self._ai_detected_indices}

        self._preview.update_redactions(local_redacted, local_detected)

    # --- Analysis ---

    def _on_analyze(self):
        if not self._pdf_processor.is_loaded:
            return

        if self._analysis_thread and self._analysis_thread.isRunning():
            return

        working = str(self._file_manager.working_copy)
        self._ner_engine.enabled_entities = self._sidebar.get_enabled_entities()

        worker = AnalysisWorker(
            self._ocr_engine, self._ner_engine,
            working, self._file_manager.is_pdf,
        )

        self._analysis_thread = QThread()
        worker.moveToThread(self._analysis_thread)
        self._analysis_thread.started.connect(worker.run)

        worker.progress.connect(self._on_analysis_progress)
        worker.finished.connect(self._on_analysis_finished)
        worker.error.connect(self._on_analysis_error)
        worker.finished.connect(self._analysis_thread.quit)
        worker.error.connect(self._analysis_thread.quit)

        self._worker = worker  # prevent GC
        self._analysis_thread.start()

    def _on_analysis_progress(self, pct: int, status: str):
        self._sidebar.set_progress(pct, status)

    def _on_analysis_finished(self, pages: list, entities: list):
        self._pages = pages
        self._entities = entities

        self._all_blocks = []
        self._page_block_offsets = []
        for page_data in self._pages:
            start = len(self._all_blocks)
            self._all_blocks.extend(page_data.blocks)
            end = len(self._all_blocks)
            self._page_block_offsets.append((start, end))

        self._ai_detected_indices = set()
        for entity in self._entities:
            for block_idx in entity.source_block_indices:
                self._ai_detected_indices.add(block_idx)

        entity_counts: dict[EntityType, int] = {}
        for e in self._entities:
            entity_counts[e.entity_type] = entity_counts.get(e.entity_type, 0) + 1

        self._sidebar.set_analysis_complete(entity_counts)
        self._render_page(self._current_page_idx)

    def _on_analysis_error(self, error_msg: str):
        self._sidebar.set_progress(0, f"Error: {error_msg}")
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed:\n{error_msg}")

    # --- Redaction ---

    def _on_block_toggled(self, local_idx: int):
        offset = self._get_global_block_offset(self._current_page_idx)
        global_idx = local_idx + offset

        if global_idx in self._redacted_block_indices:
            self._redacted_block_indices.discard(global_idx)
        else:
            self._redacted_block_indices.add(global_idx)

        self._update_preview_overlays()

    def _on_redact_all_detected(self):
        self._redacted_block_indices.update(self._ai_detected_indices)
        self._update_preview_overlays()

    def _on_clear_redactions(self):
        self._redacted_block_indices.clear()
        self._update_preview_overlays()

    # --- Export ---

    def _on_export(self):
        if not self._pdf_processor.is_loaded:
            return

        if not self._redacted_block_indices:
            reply = QMessageBox.question(
                self, "No Redactions",
                "No redactions have been applied. Export the document as-is?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        default_path = self._file_manager.get_default_export_path()
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Export Sanitized Document",
            default_path,
            "PDF Files (*.pdf)",
        )
        if not output_path:
            return

        self._sidebar.set_progress(10, "Applying redactions...")
        QApplication.processEvents()

        redaction_areas: list[RedactionArea] = []
        for global_idx in sorted(self._redacted_block_indices):
            if global_idx < len(self._all_blocks):
                block = self._all_blocks[global_idx]
                areas = self._pdf_processor.blocks_to_redaction_areas([block])
                redaction_areas.extend(areas)

        if redaction_areas:
            def redact_progress(current, total):
                pct = int(10 + (current / max(total, 1)) * 50)
                self._sidebar.set_progress(pct, f"Redacting page {current}/{total}")
                QApplication.processEvents()

            success = self._pdf_processor.apply_redactions(redaction_areas, redact_progress)
            if not success:
                QMessageBox.critical(self, "Error", "Failed to apply redactions.")
                return

        self._sidebar.set_progress(70, "Flattening document...")
        QApplication.processEvents()

        self._pdf_processor.flatten()

        self._sidebar.set_progress(90, "Exporting...")
        QApplication.processEvents()

        success = self._pdf_processor.export(output_path)
        if success:
            self._sidebar.set_progress(100, f"Exported to {os.path.basename(output_path)}")
            QMessageBox.information(
                self, "Export Complete",
                f"Sanitized document saved to:\n{output_path}\n\n"
                "The original file has not been modified."
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to export the document.")

    # --- Navigation ---

    def _on_prev_page(self):
        if self._current_page_idx > 0:
            self._render_page(self._current_page_idx - 1)

    def _on_next_page(self):
        if self._current_page_idx < self._pdf_processor.page_count - 1:
            self._render_page(self._current_page_idx + 1)

    # --- Settings ---

    def _on_locale_changed(self, locale: str):
        self._ner_engine.locale = locale
        self._ocr_engine.lang = {
            "it": "ita+eng", "en": "eng", "de": "deu+eng",
            "fr": "fra+eng", "es": "spa+eng",
        }.get(locale, "eng")

    def _on_presets_changed(self, enabled: set):
        self._ner_engine.enabled_entities = enabled

    # --- Helpers ---

    def _reset_state(self):
        self._pages = []
        self._entities = []
        self._all_blocks = []
        self._page_block_offsets = []
        self._redacted_block_indices.clear()
        self._ai_detected_indices.clear()
        self._current_page_idx = 0
        self._pdf_processor.close()
        self._file_manager.cleanup()

    def _show_about(self):
        QMessageBox.about(
            self, "About AI Document Redactor Pro",
            "<h2>AI Document Redactor Pro</h2>"
            "<p>Version 1.0.0</p>"
            "<p>100% Offline Document Redaction Tool</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>AI-powered sensitive data detection (NER)</li>"
            "<li>True content-stream redaction (not just overlay)</li>"
            "<li>PDF flattening to prevent forensic recovery</li>"
            "<li>Original file integrity guaranteed</li>"
            "<li>Multi-language support</li>"
            "</ul>"
            "<p><b>Privacy-First:</b> No data ever leaves your device.</p>"
        )

    def closeEvent(self, event):
        self._file_manager.cleanup()
        self._pdf_processor.close()
        super().closeEvent(event)
