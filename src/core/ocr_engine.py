"""
OCR Engine - Extracts text with bounding boxes from PDFs and images.
Uses PyMuPDF native extraction + Tesseract OCR fallback.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class TextBlock:
    """A word/token with its bounding box on a page."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int = 0
    confidence: float = 1.0

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
    """All extracted data for a single page."""
    page_number: int
    width: float
    height: float
    blocks: list[TextBlock] = field(default_factory=list)


class OCREngine:
    """Text extraction from PDFs/images."""

    def __init__(self, tesseract_path: Optional[str] = None, lang: str = "ita+eng"):
        self._lang = lang
        if tesseract_path and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_from_pdf(self, pdf_path: str, progress_cb=None) -> list[PageData]:
        doc = fitz.open(pdf_path)
        pages: list[PageData] = []

        for idx in range(len(doc)):
            page = doc[idx]
            pd = PageData(page_number=idx, width=page.rect.width, height=page.rect.height)

            # Native text extraction
            words = page.get_text("words")
            for w in words:
                x0, y0, x1, y1, text, *_ = w
                if text.strip():
                    pd.blocks.append(TextBlock(
                        text=text.strip(), x0=x0, y0=y0, x1=x1, y1=y1,
                        page=idx, confidence=1.0,
                    ))

            # OCR fallback if page has very little text
            if len(pd.blocks) < 3 and TESSERACT_AVAILABLE:
                ocr_blocks = self._ocr_page(page, idx)
                if len(ocr_blocks) > len(pd.blocks):
                    pd.blocks = ocr_blocks

            pages.append(pd)
            if progress_cb:
                progress_cb(idx + 1, len(doc))

        doc.close()
        return pages

    def extract_from_image(self, image_path: str) -> PageData:
        img = Image.open(image_path)
        pd = PageData(page_number=0, width=img.width, height=img.height)
        if TESSERACT_AVAILABLE:
            pd.blocks = self._ocr_image(img, page=0)
        return pd

    def _ocr_page(self, page: fitz.Page, page_idx: int) -> list[TextBlock]:
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height
        blocks = self._ocr_image(img, page_idx)
        for b in blocks:
            b.x0 *= scale_x
            b.y0 *= scale_y
            b.x1 *= scale_x
            b.y1 *= scale_y
        return blocks

    def _ocr_image(self, img: Image.Image, page: int = 0) -> list[TextBlock]:
        data = pytesseract.image_to_data(img, lang=self._lang, output_type=pytesseract.Output.DICT)
        blocks: list[TextBlock] = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if text and conf > 30:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                blocks.append(TextBlock(
                    text=text, x0=x, y0=y, x1=x + w, y1=y + h,
                    page=page, confidence=conf / 100.0,
                ))
        return blocks
