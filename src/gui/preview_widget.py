"""
Preview Widget - Interactive document preview with clickable redaction.
Users can click on words to manually toggle redaction.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QBrush,
    QMouseEvent, QWheelEvent, QFont,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame,
)

from core.ocr_engine import TextBlock

logger = logging.getLogger(__name__)


class PageCanvas(QWidget):
    """Canvas that renders a PDF page and overlays redaction rectangles."""

    block_clicked = pyqtSignal(int)  # emits block index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._blocks: list[TextBlock] = []
        self._redacted_indices: set[int] = set()
        self._ai_detected_indices: set[int] = set()
        self._hovered_index: Optional[int] = None
        self._zoom: float = 1.0
        self._render_scale: float = 1.0  # pixmap-to-PDF coordinate scale
        self.setMouseTracking(True)

    def set_page(self, pixmap: QPixmap, blocks: list[TextBlock],
                 render_scale: float = 1.0):
        self._pixmap = pixmap
        self._blocks = blocks
        self._render_scale = render_scale
        self._update_size()
        self.update()

    def set_redacted(self, indices: set[int]):
        self._redacted_indices = indices
        self.update()

    def set_ai_detected(self, indices: set[int]):
        self._ai_detected_indices = indices
        self.update()

    def set_zoom(self, zoom: float):
        self._zoom = max(0.25, min(zoom, 4.0))
        self._update_size()
        self.update()

    @property
    def zoom(self) -> float:
        return self._zoom

    def _update_size(self):
        if self._pixmap:
            w = int(self._pixmap.width() * self._zoom)
            h = int(self._pixmap.height() * self._zoom)
            self.setFixedSize(w, h)

    def paintEvent(self, event):
        if not self._pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(0, 0, scaled)

        s = self._render_scale * self._zoom  # total scale: PDF coords -> screen

        for idx, block in enumerate(self._blocks):
            padding = 1.0
            rect = QRectF(
                (block.x0 - padding) * s,
                (block.y0 - padding) * s,
                (block.width + padding * 2) * s,
                (block.height + padding * 2) * s,
            )

            if idx in self._redacted_indices:
                painter.fillRect(rect, QColor(0, 0, 0, 240))
            elif idx in self._ai_detected_indices:
                painter.setPen(QPen(QColor("#ef4444"), 2))
                painter.setBrush(QBrush(QColor(239, 68, 68, 40)))
                painter.drawRect(rect)
            elif idx == self._hovered_index:
                painter.setPen(QPen(QColor("#2563eb"), 1.5))
                painter.setBrush(QBrush(QColor(37, 99, 235, 30)))
                painter.drawRect(rect)

        painter.end()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        old_hover = self._hovered_index
        self._hovered_index = self._hit_test(pos)
        if old_hover != self._hovered_index:
            self.update()
            if self._hovered_index is not None:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            idx = self._hit_test(pos)
            if idx is not None:
                self.block_clicked.emit(idx)

    def _hit_test(self, pos: QPointF) -> Optional[int]:
        s = self._render_scale * self._zoom
        x = pos.x() / s
        y = pos.y() / s
        for idx, block in enumerate(self._blocks):
            if block.x0 <= x <= block.x1 and block.y0 <= y <= block.y1:
                return idx
        return None


class PreviewWidget(QFrame):
    """Document preview panel with zoom controls and page navigation."""

    block_toggled = pyqtSignal(int)  # emits block index when user clicks a word

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 0
        self._total_pages = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)

        self._zoom_out_btn = QPushButton("-")
        self._zoom_out_btn.setFixedSize(32, 32)
        self._zoom_out_btn.setObjectName("secondaryButton")
        self._zoom_out_btn.clicked.connect(self._zoom_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(60)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(32, 32)
        self._zoom_in_btn.setObjectName("secondaryButton")
        self._zoom_in_btn.clicked.connect(self._zoom_in)

        toolbar.addStretch()

        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedSize(32, 32)
        self._prev_btn.setObjectName("secondaryButton")
        self._prev_btn.clicked.connect(self._prev_page)

        self._page_label = QLabel("Page 0/0")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setFixedWidth(100)

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedSize(32, 32)
        self._next_btn.setObjectName("secondaryButton")
        self._next_btn.clicked.connect(self._next_page)

        toolbar.addWidget(self._prev_btn)
        toolbar.addWidget(self._page_label)
        toolbar.addWidget(self._next_btn)
        toolbar.addStretch()
        toolbar.addWidget(self._zoom_out_btn)
        toolbar.addWidget(self._zoom_label)
        toolbar.addWidget(self._zoom_in_btn)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("topBar")
        toolbar_frame.setLayout(toolbar)
        toolbar_frame.setFixedHeight(44)
        layout.addWidget(toolbar_frame)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #0f0f23; }")

        self._canvas = PageCanvas()
        self._canvas.block_clicked.connect(self._on_block_clicked)
        self._scroll_area.setWidget(self._canvas)

        layout.addWidget(self._scroll_area)

    def display_page(self, pixmap: QPixmap, blocks: list[TextBlock],
                     page_idx: int, total_pages: int,
                     render_scale: float = 1.0):
        self._current_page = page_idx
        self._total_pages = total_pages
        self._canvas.set_page(pixmap, blocks, render_scale)
        self._page_label.setText(f"Page {page_idx + 1}/{total_pages}")

    def update_redactions(self, redacted: set[int], ai_detected: set[int]):
        self._canvas.set_redacted(redacted)
        self._canvas.set_ai_detected(ai_detected)

    def _on_block_clicked(self, idx: int):
        self.block_toggled.emit(idx)

    def _zoom_in(self):
        z = self._canvas.zoom * 1.25
        self._canvas.set_zoom(z)
        self._zoom_label.setText(f"{int(z * 100)}%")

    def _zoom_out(self):
        z = self._canvas.zoom / 1.25
        self._canvas.set_zoom(z)
        self._zoom_label.setText(f"{int(z * 100)}%")

    def _prev_page(self):
        pass  # handled by main window connecting to this

    def _next_page(self):
        pass  # handled by main window connecting to this

    @property
    def prev_button(self):
        return self._prev_btn

    @property
    def next_button(self):
        return self._next_btn

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
