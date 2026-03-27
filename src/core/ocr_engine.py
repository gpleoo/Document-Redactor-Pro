"""
OCR Engine Module - Extracts text and bounding boxes from images and PDFs.
Supports Tesseract OCR with offline processing.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed; OCR on images will be unavailable")


@dataclass
class TextBlock:
    """Represents a detected text block with its bounding box."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int = 0
    confidence: float = 0.0
    source: str = "native"  # "native" for PDF text, "ocr" for OCR-extracted

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass
class PageData:
    """Holds extracted data for a single page."""
    page_number: int
    width: float
    height: float
    blocks: list[TextBlock] = field(default_factory=list)
    image: Optional[Image.Image] = None


class OCREngine:
    """Handles text extraction from PDFs and images using native text
    extraction and Tesseract OCR fallback."""

    DEFAULT_DPI = 300
    DEFAULT_LANG = "eng+ita"

    def __init__(self, tesseract_path: Optional[str] = None, lang: str = DEFAULT_LANG):
        self._lang = lang
        if tesseract_path and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self._dpi = self.DEFAULT_DPI

    @property
    def lang(self) -> str:
        return self._lang

    @lang.setter
    def lang(self, value: str) -> None:
        self._lang = value

    def extract_from_pdf(self, pdf_path: str, progress_callback=None) -> list[PageData]:
        """Extract text blocks from all pages of a PDF.

        First attempts native text extraction via PyMuPDF.
        Falls back to OCR for pages with little or no native text.
        """
        doc = fitz.open(pdf_path)
        pages: list[PageData] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_data = PageData(
                page_number=page_idx,
                width=page.rect.width,
                height=page.rect.height,
            )

            native_blocks = self._extract_native_text(page, page_idx)
            page_data.blocks.extend(native_blocks)

            if self._needs_ocr(native_blocks, page):
                ocr_blocks = self._extract_ocr_from_page(page, page_idx)
                page_data.blocks.extend(ocr_blocks)

            pages.append(page_data)

            if progress_callback:
                progress_callback(page_idx + 1, len(doc))

        doc.close()
        return pages

    def extract_from_image(self, image_path: str) -> PageData:
        """Extract text blocks from a single image file via OCR."""
        img = Image.open(image_path)
        page_data = PageData(
            page_number=0,
            width=img.width,
            height=img.height,
            image=img,
        )

        if TESSERACT_AVAILABLE:
            blocks = self._run_tesseract(img, page=0)
            page_data.blocks.extend(blocks)
        else:
            logger.error("Tesseract not available for image OCR")

        return page_data

    def _extract_native_text(self, page: fitz.Page, page_idx: int) -> list[TextBlock]:
        """Extract text with bounding boxes from PDF page using PyMuPDF."""
        blocks: list[TextBlock] = []
        word_list = page.get_text("words")

        for w in word_list:
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            if text.strip():
                blocks.append(TextBlock(
                    text=text.strip(),
                    x0=x0, y0=y0, x1=x1, y1=y1,
                    page=page_idx,
                    confidence=1.0,
                    source="native",
                ))
        return blocks

    def _needs_ocr(self, native_blocks: list[TextBlock], page: fitz.Page) -> bool:
        """Determine if a page has insufficient native text and needs OCR."""
        if not native_blocks:
            return True
        total_text = " ".join(b.text for b in native_blocks)
        page_area = page.rect.width * page.rect.height
        text_density = len(total_text) / max(page_area, 1)
        return text_density < 0.0001

    def _extract_ocr_from_page(self, page: fitz.Page, page_idx: int) -> list[TextBlock]:
        """Render a PDF page to image and run OCR."""
        if not TESSERACT_AVAILABLE:
            return []

        mat = fitz.Matrix(self._dpi / 72, self._dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height

        raw_blocks = self._run_tesseract(img, page=page_idx)
        for block in raw_blocks:
            block.x0 *= scale_x
            block.y0 *= scale_y
            block.x1 *= scale_x
            block.y1 *= scale_y

        return raw_blocks

    def _run_tesseract(self, img: Image.Image, page: int = 0) -> list[TextBlock]:
        """Run Tesseract OCR on a PIL Image and return TextBlocks."""
        if not TESSERACT_AVAILABLE:
            return []

        data = pytesseract.image_to_data(
            img, lang=self._lang, output_type=pytesseract.Output.DICT
        )
        blocks: list[TextBlock] = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if text and conf > 30:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                blocks.append(TextBlock(
                    text=text,
                    x0=x, y0=y, x1=x + w, y1=y + h,
                    page=page,
                    confidence=conf / 100.0,
                    source="ocr",
                ))
        return blocks
