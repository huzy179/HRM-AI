from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class JDRequirements:
    required_skills: list[str]
    min_years: float


SKILL_KEYWORDS = [
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


def extract_jd_requirements(jd_text: str) -> JDRequirements:
    t = (jd_text or "").lower()
    required_skills = sorted({kw for kw in SKILL_KEYWORDS if kw in t})

    min_years = 0.0
    # English patterns
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b", t):
        try:
            min_years = max(min_years, float(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", t):
        try:
            min_years = max(min_years, float(m.group(1)))
        except Exception:
            pass

    # Vietnamese patterns
    for m in re.finditer(r"tối thiểu\s*(\d+(?:\.\d+)?)\s*năm", t):
        try:
            min_years = max(min_years, float(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*\+\s*năm", t):
        try:
            min_years = max(min_years, float(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*năm\s*kinh nghiệm", t):
        try:
            min_years = max(min_years, float(m.group(1)))
        except Exception:
            pass

    return JDRequirements(required_skills=required_skills, min_years=float(min_years))

