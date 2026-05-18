from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(\+?84|0)\s*(\d[\d\s().-]{7,}\d)")


@dataclass(frozen=True)
class CandidateProfileExtracted:
    name: str = ""
    email: str = ""
    phone: str = ""
    years_experience: float = 0.0
    education: str = ""
    skills: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.skills is None:
            object.__setattr__(self, "skills", [])


_SKILL_KEYWORDS = [
    "python",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgres",
    "mysql",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "langchain",
    "rag",
    "llm",
    "pandas",
    "numpy",
    "opencv",
]


def _first_non_empty_line(text: str) -> str:
    for line in (text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _extract_years(text: str) -> float:
    t = (text or "").lower()
    candidates: list[float] = []

    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", t):
        try:
            candidates.append(float(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*năm\b", t):
        try:
            candidates.append(float(m.group(1)))
        except Exception:
            pass

    if not candidates:
        return 0.0
    # choose a conservative max but cap at 50
    return float(max(0.0, min(50.0, max(candidates))))


def extract_candidate_profile(text: str) -> CandidateProfileExtracted:
    t = text or ""

    email = ""
    m = _EMAIL_RE.search(t)
    if m:
        email = m.group(0).strip()

    phone = ""
    m2 = _PHONE_RE.search(t)
    if m2:
        phone = (m2.group(0) or "").strip()

    # naive name heuristic: first non-empty line, filtered for noise
    name = _first_non_empty_line(t)
    if len(name) > 80 or ("@" in name) or any(k in name.lower() for k in ["curriculum", "resume", "cv"]):
        name = ""

    years = _extract_years(t)

    lower = t.lower()
    skills: list[str] = []
    for kw in _SKILL_KEYWORDS:
        if kw in lower:
            skills.append(kw)
    skills = sorted(set(skills))

    education = ""
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(x in s.lower() for x in ["university", "college", "đại học", "cao đẳng", "bachelor", "master"]):
            education = s[:400]
            break

    return CandidateProfileExtracted(
        name=name,
        email=email,
        phone=phone,
        years_experience=years,
        education=education,
        skills=skills,
    )

