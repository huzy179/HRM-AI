from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from backend.services.cv_parser import parse_cv


def _make_pdf_with_text(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path.as_posix())
    doc.close()


def test_parse_cv_extracts_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf_with_text(pdf_path, "Hello CV Parser")

    result = parse_cv(pdf_path)
    assert result.error is None
    assert "Hello CV Parser" in result.raw_text
