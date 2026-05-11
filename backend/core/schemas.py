from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CVExtracted:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CVParseResult:
    cv_id: str
    raw_text: str
    extracted: CVExtracted = field(default_factory=CVExtracted)
    error: Optional[str] = None
    method: str = "unknown"  # pymupdf | pdfplumber | ocr_pdf | ocr_image | unknown


@dataclass(frozen=True)
class CVRankResult:
    cv_id: str
    score: float
    status: str  # "OK" | "ERROR"
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CVLLMReview:
    cv_id: str
    score: int  # 0-100
    summary: str
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
