"""
Drop Zone Widget - Drag & drop area for loading files.
Beautiful animated landing zone with file type icons.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QFont
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog

from core.file_manager import SUPPORTED_EXTENSIONS


class DropZone(QFrame):
    """Drag-and-drop area for loading PDF/image files."""

    file_dropped = pyqtSignal(str)  # Emitted with file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Icon
        icon_label = QLabel("\U0001f4c4")  # document emoji as placeholder
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont("Segoe UI Emoji", 48))
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)

        # Title
        title = QLabel("Trascina qui il tuo documento")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("PDF, JPG, PNG supportati")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent; border: none;")
        layout.addWidget(subtitle)

        # Browse button
        browse_btn = QPushButton("  Sfoglia File  ")
        browse_btn.setObjectName("primary")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _browse_file(self):
        exts = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri Documento", "",
            f"Documenti ({exts});;Tutti i file (*)",
        )
        if path:
            self.file_dropped.emit(path)

    # ── Drag & Drop ──────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.setStyleSheet(
                    self.styleSheet()
                    + "QFrame#dropZone { border-color: #2563eb; background-color: #1e3a5f; }"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")  # Reset to theme default

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.file_dropped.emit(path)
