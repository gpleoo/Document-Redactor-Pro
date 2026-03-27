"""
Drop Zone Widget - Drag & drop area for loading documents.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QFont
from PyQt6.QtWidgets import QFrame

from ..core.file_manager import SUPPORTED_EXTENSIONS


class DropZoneWidget(QFrame):
    """Central drag & drop zone for loading files."""

    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self._hovering = False
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet("""
            DropZoneWidget {
                background-color: #1e1e3a;
                border: 2px dashed #334155;
                border-radius: 16px;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_supported(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._hovering = True
                self.update()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._hovering = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._hovering = False
        self.update()
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self._is_supported(file_path):
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def _is_supported(self, path: str) -> bool:
        import os
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_EXTENSIONS

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        if self._hovering:
            pen = QPen(QColor("#2563eb"), 3, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(4, 4, -4, -4), 16, 16)

        # Draw icon
        icon_font = QFont("Segoe UI", 48)
        painter.setFont(icon_font)
        painter.setPen(QColor("#2563eb" if self._hovering else "#475569"))
        painter.drawText(rect.adjusted(0, -40, 0, 0), Qt.AlignmentFlag.AlignCenter, "\u21e7")

        # Draw text
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(rect.adjusted(0, 20, 0, 0), Qt.AlignmentFlag.AlignCenter,
                         "Drag & Drop File Here")

        sub_font = QFont("Segoe UI", 11)
        painter.setFont(sub_font)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(rect.adjusted(0, 55, 0, 0), Qt.AlignmentFlag.AlignCenter,
                         "Supported: PDF, JPG, PNG")

        painter.end()
