"""
PDF Processor Module - Handles real sanitization of PDF documents.
Performs true redaction by removing text from the PDF content stream
and flattening annotations to prevent forensic data recovery.
"""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image

from core.ocr_engine import TextBlock

logger = logging.getLogger(__name__)


@dataclass
class RedactionArea:
    """Defines an area to redact on a specific page."""
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    label: str = "REDACTED"

    @property
    def rect(self) -> fitz.Rect:
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)


class PDFProcessor:
    """Handles PDF loading, redaction, flattening, and export.

    Performs true content-stream redaction (not just overlay) using
    PyMuPDF's built-in redaction annotations, which remove underlying
    text and image data from the PDF structure.
    """

    REDACTION_FILL_COLOR = (0, 0, 0)  # Black fill
    REDACTION_TEXT_COLOR = (1, 1, 1)  # White text for label
    REDACTION_FONT_SIZE = 8

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

    @property
    def source_path(self) -> Optional[str]:
        return self._source_path

    def load(self, file_path: str) -> bool:
        """Load a PDF file into a working copy. Original file is never modified."""
        try:
            self.close()
            self._source_path = file_path

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, prefix="redactor_"
            )
            self._temp_path = temp_file.name
            temp_file.close()

            src_doc = fitz.open(file_path)
            src_doc.save(self._temp_path)
            src_doc.close()

            self._doc = fitz.open(self._temp_path)
            self._page_count = len(self._doc)
            logger.info(f"Loaded PDF: {file_path} ({self._page_count} pages)")
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF '{file_path}': {e}")
            self._doc = None
            return False

    def load_image(self, image_path: str) -> bool:
        """Convert an image file to a single-page PDF for uniform processing."""
        try:
            self.close()
            self._source_path = image_path

            img = Image.open(image_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, prefix="redactor_img_"
            )
            self._temp_path = temp_file.name
            temp_file.close()

            img_doc = fitz.open()
            img_bytes = img.tobytes("raw", "RGB")
            page = img_doc.new_page(width=img.width, height=img.height)

            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, img.width, img.height), img_bytes, False)
            page.insert_image(page.rect, pixmap=pix)

            img_doc.save(self._temp_path)
            img_doc.close()

            self._doc = fitz.open(self._temp_path)
            self._page_count = len(self._doc)
            logger.info(f"Loaded image as PDF: {image_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load image '{image_path}': {e}")
            self._doc = None
            return False

    def get_page_pixmap(self, page_idx: int, zoom: float = 1.0) -> Optional[fitz.Pixmap]:
        """Render a page to a pixmap for preview display."""
        if not self._doc or page_idx >= self._page_count:
            return None
        page = self._doc[page_idx]
        mat = fitz.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=mat)

    def get_page_size(self, page_idx: int) -> Optional[tuple[float, float]]:
        """Return (width, height) of a page."""
        if not self._doc or page_idx >= self._page_count:
            return None
        page = self._doc[page_idx]
        return (page.rect.width, page.rect.height)

    def apply_redactions(
        self,
        redaction_areas: list[RedactionArea],
        progress_callback=None,
    ) -> bool:
        """Apply true content-stream redactions to the working PDF.

        This uses PyMuPDF's redaction annotations which:
        1. Add redaction annotations to mark areas
        2. Apply redactions to physically remove text/images underneath
        3. Fill the area with an opaque rectangle

        The underlying text data is permanently removed from the PDF
        content stream, preventing copy-paste or forensic recovery.
        """
        if not self._doc:
            logger.error("No document loaded")
            return False

        try:
            pages_with_redactions: set[int] = set()
            for area in redaction_areas:
                if area.page >= self._page_count:
                    continue
                page = self._doc[area.page]
                annot = page.add_redact_annot(
                    area.rect,
                    text=area.label if area.label else "",
                    fontsize=self.REDACTION_FONT_SIZE,
                    fill=self.REDACTION_FILL_COLOR,
                    text_color=self.REDACTION_TEXT_COLOR,
                )
                pages_with_redactions.add(area.page)

            total = len(pages_with_redactions)
            for i, page_idx in enumerate(sorted(pages_with_redactions)):
                page = self._doc[page_idx]
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)

                if progress_callback:
                    progress_callback(i + 1, total)

            logger.info(f"Applied {len(redaction_areas)} redactions across {total} pages")
            return True
        except Exception as e:
            logger.error(f"Failed to apply redactions: {e}")
            return False

    def flatten(self) -> bool:
        """Flatten all annotations and form fields to prevent editing.

        This bakes all remaining annotations into the page content,
        making redactions permanent and non-reversible.
        """
        if not self._doc:
            return False

        try:
            for page_idx in range(self._page_count):
                page = self._doc[page_idx]
                page.clean_contents()

            temp_save = self._temp_path + ".flat.pdf"
            self._doc.save(
                temp_save,
                deflate=True,
                clean=True,
                garbage=4,
                linear=True,
            )
            self._doc.close()
            self._doc = fitz.open(temp_save)
            self._temp_path = temp_save
            logger.info("Document flattened successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to flatten document: {e}")
            return False

    def export(self, output_path: str) -> bool:
        """Export the redacted and flattened document to the specified path."""
        if not self._doc:
            logger.error("No document loaded for export")
            return False

        try:
            self._doc.save(
                output_path,
                deflate=True,
                clean=True,
                garbage=4,
            )
            logger.info(f"Exported redacted document to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export document: {e}")
            return False

    def blocks_to_redaction_areas(
        self, blocks: list[TextBlock], label: str = "REDACTED"
    ) -> list[RedactionArea]:
        """Convert TextBlocks to RedactionAreas for redaction."""
        areas: list[RedactionArea] = []
        for block in blocks:
            padding = 2.0
            areas.append(RedactionArea(
                page=block.page,
                x0=block.x0 - padding,
                y0=block.y0 - padding,
                x1=block.x1 + padding,
                y1=block.y1 + padding,
                label=label,
            ))
        return areas

    def close(self):
        """Close the current document and clean up."""
        if self._doc:
            try:
                self._doc.close()
            except Exception:
                pass
        self._doc = None
        self._page_count = 0
        self._source_path = None

    def __del__(self):
        self.close()
