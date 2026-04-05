"""
Preview Widget - Interactive PDF/image preview with redaction overlays.
Handles zoom, scrolling, click-to-select, and overlay rendering.
render_scale is critical: pixmap at 1.5x but block coords in PDF space.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QImage, QPen, QBrush, QFont, QWheelEvent,
)
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame,
)

from gui.theme import Colors

RENDER_SCALE = 1.5  # Pixmap render resolution multiplier


class PageCanvas(QWidget):
    """Renders a single page with overlays for redacted blocks."""

    block_clicked = pyqtSignal(int, int)  # (page_index, block_index_in_page)

    def __init__(self, page_index: int, parent=None):
        super().__init__(parent)
        self._page_index = page_index
        self._pixmap: QPixmap | None = None
        self._zoom = 1.0
        self._blocks = []           # list of TextBlock
        self._selected_indices = set()  # indices into _blocks that are selected for redaction
        self._hover_index = -1
        self._redaction_style = "black"   # "black", "white", "custom"
        self._custom_text = ""
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self._update_size()

    def set_blocks(self, blocks: list):
        self._blocks = blocks

    def set_selected(self, indices: set):
        self._selected_indices = indices
        self.update()

    def set_zoom(self, zoom: float):
        self._zoom = zoom
        self._update_size()

    def set_redaction_style(self, style: str, custom_text: str = ""):
        self._redaction_style = style
        self._custom_text = custom_text
        self.update()

    def _update_size(self):
        if self._pixmap:
            w = int(self._pixmap.width() * self._zoom / RENDER_SCALE)
            h = int(self._pixmap.height() * self._zoom / RENDER_SCALE)
            self.setFixedSize(w, h)
        self.update()

    def paintEvent(self, event):
        if not self._pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw page
        scale = self._zoom / RENDER_SCALE
        target = QRectF(0, 0, self._pixmap.width() * scale, self._pixmap.height() * scale)
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))

        s = RENDER_SCALE * self._zoom  # Coordinate multiplier: PDF coords → widget coords
        pad = 1.0

        # Draw overlays for selected blocks
        for idx, block in enumerate(self._blocks):
            if idx in self._selected_indices:
                x = (block.x0 - pad) * s
                y = (block.y0 - pad) * s
                w = (block.x1 - block.x0 + 2 * pad) * s
                h = (block.y1 - block.y0 + 2 * pad) * s
                rect = QRectF(x, y, w, h)

                if self._redaction_style == "black":
                    painter.fillRect(rect, QColor(0, 0, 0, 255))
                elif self._redaction_style == "white":
                    painter.fillRect(rect, QColor(255, 255, 255, 255))
                elif self._redaction_style == "custom":
                    painter.fillRect(rect, QColor(255, 255, 255, 255))
                    if self._custom_text:
                        painter.setPen(QColor(0, 0, 0))
                        font = QFont("Arial", max(7, int(h * 0.5)))
                        painter.setFont(font)
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._custom_text)

            elif idx == self._hover_index:
                # Hover highlight
                x = (block.x0 - pad) * s
                y = (block.y0 - pad) * s
                w = (block.x1 - block.x0 + 2 * pad) * s
                h = (block.y1 - block.y0 + 2 * pad) * s
                rect = QRectF(x, y, w, h)
                painter.fillRect(rect, QColor(37, 99, 235, 50))
                painter.setPen(QPen(QColor(37, 99, 235, 120), 1.5))
                painter.drawRect(rect)

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position()
        s = RENDER_SCALE * self._zoom
        # Convert widget coords → PDF coords
        pdf_x = pos.x() / s
        pdf_y = pos.y() / s

        new_hover = -1
        for idx, block in enumerate(self._blocks):
            if block.x0 <= pdf_x <= block.x1 and block.y0 <= pdf_y <= block.y1:
                new_hover = idx
                break

        if new_hover != self._hover_index:
            self._hover_index = new_hover
            self.setCursor(
                Qt.CursorShape.PointingHandCursor if new_hover >= 0
                else Qt.CursorShape.ArrowCursor
            )
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hover_index >= 0:
            self.block_clicked.emit(self._page_index, self._hover_index)

    def leaveEvent(self, event):
        if self._hover_index >= 0:
            self._hover_index = -1
            self.update()


class PreviewWidget(QScrollArea):
    """Scrollable preview showing all pages with zoom controls."""

    block_clicked = pyqtSignal(int, int)  # (page_index, block_index_in_page)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._zoom = 1.0
        self._canvases: list[PageCanvas] = []
        self._redaction_style = "black"
        self._custom_text = ""

        # Container
        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self.setWidget(container)

        # Zoom controls bar
        self._zoom_bar = self._create_zoom_bar()

    def _create_zoom_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setStyleSheet(
            f"background: {Colors.BG_DARK}; border: 1px solid {Colors.BORDER}; "
            f"border-radius: 8px; padding: 4px;"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(6)

        btn_out = QPushButton("-")
        btn_out.setObjectName("small")
        btn_out.setFixedSize(28, 28)
        btn_out.clicked.connect(lambda: self.set_zoom(self._zoom - 0.1))

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(50)
        self._zoom_label.setStyleSheet("background: transparent; border: none;")

        btn_in = QPushButton("+")
        btn_in.setObjectName("small")
        btn_in.setFixedSize(28, 28)
        btn_in.clicked.connect(lambda: self.set_zoom(self._zoom + 0.1))

        btn_fit = QPushButton("Fit")
        btn_fit.setObjectName("small")
        btn_fit.setFixedWidth(40)
        btn_fit.clicked.connect(self._fit_width)

        h.addWidget(btn_out)
        h.addWidget(self._zoom_label)
        h.addWidget(btn_in)
        h.addWidget(btn_fit)

        bar.setFixedSize(180, 36)
        bar.move(10, 10)
        bar.raise_()
        return bar

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._zoom_bar.move(self.width() - self._zoom_bar.width() - 20, 10)

    def clear_pages(self):
        self._canvases.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_page(self, pixmap: QPixmap, blocks: list, page_index: int):
        canvas = PageCanvas(page_index)
        canvas.set_pixmap(pixmap)
        canvas.set_blocks(blocks)
        canvas.set_zoom(self._zoom)
        canvas.set_redaction_style(self._redaction_style, self._custom_text)
        canvas.block_clicked.connect(self.block_clicked.emit)
        self._canvases.append(canvas)

        # Page label
        page_label = QLabel(f"Pagina {page_index + 1}")
        page_label.setObjectName("subtitle")
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_label.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")

        self._layout.addWidget(page_label)
        self._layout.addWidget(canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

    def set_zoom(self, zoom: float):
        self._zoom = max(0.3, min(3.0, zoom))
        self._zoom_label.setText(f"{int(self._zoom * 100)}%")
        for canvas in self._canvases:
            canvas.set_zoom(self._zoom)

    def _fit_width(self):
        if self._canvases:
            available = self.viewport().width() - 60
            canvas = self._canvases[0]
            if canvas._pixmap:
                page_w = canvas._pixmap.width() / RENDER_SCALE
                if page_w > 0:
                    self.set_zoom(available / page_w)

    def set_selected_blocks(self, page_idx: int, block_indices: set):
        if 0 <= page_idx < len(self._canvases):
            self._canvases[page_idx].set_selected(block_indices)

    def set_all_selections(self, selections: dict[int, set]):
        """selections: {page_idx: set of block indices}."""
        for canvas in self._canvases:
            canvas.set_selected(set())
        for page_idx, indices in selections.items():
            if 0 <= page_idx < len(self._canvases):
                self._canvases[page_idx].set_selected(indices)

    def set_redaction_style(self, style: str, custom_text: str = ""):
        self._redaction_style = style
        self._custom_text = custom_text
        for canvas in self._canvases:
            canvas.set_redaction_style(style, custom_text)

    def scroll_to_page(self, page_idx: int):
        if 0 <= page_idx < len(self._canvases):
            self.ensureWidgetVisible(self._canvases[page_idx])

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            self.set_zoom(self._zoom + (0.05 if delta > 0 else -0.05))
            event.accept()
        else:
            super().wheelEvent(event)
