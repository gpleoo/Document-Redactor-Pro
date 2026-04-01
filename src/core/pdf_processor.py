"""
PDF Processor - True content-stream redaction + flattening.
Removes text from PDF structure, not just overlay.
"""

import logging
import tempfile
from dataclasses import dataclass
from typing import Optional

import fitz
from PIL import Image

from core.ocr_engine import TextBlock

logger = logging.getLogger(__name__)


@dataclass
class RedactionArea:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    fill_color: tuple[float, float, float] = (0, 0, 0)
    text_color: tuple[float, float, float] = (1, 1, 1)
    replacement_text: str = ""

    @property
    def rect(self) -> fitz.Rect:
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)


class PDFProcessor:
    """Handles PDF loading, true redaction, flattening, and export."""

    def __init__(self):
        self._doc: Optional[fitz.Document] = None
        self._source_path: Optional[str] = None
        self._temp_path: Optional[str] = None
        self._page_count: int = 0

    @property
    def is_loaded(self) -> bool:
        return self._doc is not None

    @property
    def page_count(self) -> int:
        return self._page_count

    def load(self, file_path: str) -> bool:
        try:
            self.close()
            self._source_path = file_path
            temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix="redactor_")
            self._temp_path = temp.name
            temp.close()
            src = fitz.open(file_path)
            src.save(self._temp_path)
            src.close()
            self._doc = fitz.open(self._temp_path)
            self._page_count = len(self._doc)
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            self._doc = None
            return False

    def load_image(self, image_path: str) -> bool:
        try:
            self.close()
            self._source_path = image_path
            img = Image.open(image_path).convert("RGB")
            temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix="redactor_img_")
            self._temp_path = temp.name
            temp.close()
            doc = fitz.open()
            page = doc.new_page(width=img.width, height=img.height)
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, img.width, img.height),
                              img.tobytes("raw", "RGB"), False)
            page.insert_image(page.rect, pixmap=pix)
            doc.save(self._temp_path)
            doc.close()
            self._doc = fitz.open(self._temp_path)
            self._page_count = len(self._doc)
            return True
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self._doc = None
            return False

    def get_page_pixmap(self, page_idx: int, zoom: float = 1.0) -> Optional[fitz.Pixmap]:
        if not self._doc or page_idx >= self._page_count:
            return None
        return self._doc[page_idx].get_pixmap(matrix=fitz.Matrix(zoom, zoom))

    def apply_redactions(self, areas: list[RedactionArea], progress_cb=None) -> bool:
        if not self._doc:
            return False
        try:
            pages_touched: set[int] = set()
            for area in areas:
                if area.page >= self._page_count:
                    continue
                page = self._doc[area.page]
                page.add_redact_annot(
                    area.rect,
                    text=area.replacement_text,
                    fontsize=8,
                    fill=area.fill_color,
                    text_color=area.text_color,
                )
                pages_touched.add(area.page)

            for i, pidx in enumerate(sorted(pages_touched)):
                self._doc[pidx].apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
                if progress_cb:
                    progress_cb(i + 1, len(pages_touched))
            return True
        except Exception as e:
            logger.error(f"Redaction failed: {e}")
            return False

    def flatten(self) -> bool:
        if not self._doc:
            return False
        try:
            for p in range(self._page_count):
                self._doc[p].clean_contents()
            flat_path = self._temp_path + ".flat.pdf"
            self._doc.save(flat_path, deflate=True, clean=True, garbage=4, linear=True)
            self._doc.close()
            self._doc = fitz.open(flat_path)
            self._temp_path = flat_path
            return True
        except Exception as e:
            logger.error(f"Flatten failed: {e}")
            return False

    def export(self, output_path: str) -> bool:
        if not self._doc:
            return False
        try:
            self._doc.save(output_path, deflate=True, clean=True, garbage=4)
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def blocks_to_areas(self, blocks: list[TextBlock],
                        fill_color=(0, 0, 0), text_color=(1, 1, 1),
                        replacement_text="") -> list[RedactionArea]:
        areas = []
        for b in blocks:
            pad = 2.0
            areas.append(RedactionArea(
                page=b.page, x0=b.x0 - pad, y0=b.y0 - pad,
                x1=b.x1 + pad, y1=b.y1 + pad,
                fill_color=fill_color, text_color=text_color,
                replacement_text=replacement_text,
            ))
        return areas

    def close(self):
        if self._doc:
            try:
                self._doc.close()
            except Exception:
                pass
        self._doc = None
        self._page_count = 0
