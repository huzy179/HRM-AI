from __future__ import annotations

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from backend.core.schemas import CVParseResult
from backend.services.utils import normalize_text


def extract_text_pymupdf(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    doc = fitz.open(path.as_posix())
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n".join(parts)
    finally:
        doc.close()


def extract_text_pdfplumber(pdf_path: str | Path) -> str:
    from pdfplumber import open as pdf_open

    path = Path(pdf_path)
    parts: list[str] = []
    with pdf_open(path.as_posix()) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def extract_text_ocr_pymupdf(pdf_path: str | Path) -> str:
    """
    OCR fallback for scanned PDFs (best-effort).

    Requires:
    - Python package `pytesseract`
    - Tesseract OCR installed on the machine.

    Optional:
    - Set `TESSERACT_CMD` env var to the full path of `tesseract.exe`.
    """
    try:
        import os

        import pytesseract
        from PIL import Image
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("OCR_DEPENDENCIES_MISSING") from exc

    tesseract_cmd = os.environ.get("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    path = Path(pdf_path)
    doc = fitz.open(path.as_posix())
    try:
        parts: list[str] = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            parts.append(pytesseract.image_to_string(img))
        return "\n".join(parts)
    finally:
        doc.close()


def parse_cv(pdf_path: str | Path, *, fallback_pdfplumber: bool = True) -> CVParseResult:
    path = Path(pdf_path)
    cv_id = path.name

    error: Optional[str] = None
    raw_text = ""
    try:
        raw_text = extract_text_pymupdf(path)
        raw_text = normalize_text(raw_text)

        if fallback_pdfplumber and not raw_text:
            raw_text = extract_text_pdfplumber(path)
            raw_text = normalize_text(raw_text)

        if not raw_text:
            try:
                raw_text = extract_text_ocr_pymupdf(path)
                raw_text = normalize_text(raw_text)
            except Exception:
                raw_text = ""

        if not raw_text:
            error = "EMPTY_TEXT_NEEDS_OCR"
    except Exception as exc:  # noqa: BLE001
        error = f"PARSE_ERROR: {exc.__class__.__name__}: {exc}"

    return CVParseResult(cv_id=cv_id, raw_text=raw_text, error=error)
