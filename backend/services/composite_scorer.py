from __future__ import annotations

import json
from dataclasses import dataclass

from backend.db import models
from backend.services.jd_requirements import extract_jd_requirements


@dataclass(frozen=True)
class RuleScore:
    score: float  # 0..100
    details: dict


def _safe_json_loads(s: str) -> object:
    try:
        return json.loads(s or "")
    except Exception:
        return None


def score_candidate_rules(
    *,
    jd_text: str,
    profile: models.CandidateProfile | None,
    required_skills_override: list[str] | None = None,
    min_years_override: float | None = None,
) -> RuleScore:
    req = extract_jd_requirements(jd_text)
    required_skills = (
        sorted({str(x).strip().lower() for x in (required_skills_override or []) if str(x).strip()})
        if required_skills_override
        else req.required_skills
    )
    min_years = float(min_years_override or 0.0) if (min_years_override or 0.0) > 0 else float(req.min_years or 0.0)

    skills_have: set[str] = set()
    years_have = 0.0
    if profile is not None:
        years_have = float(profile.years_experience or 0.0)
        skills_obj = _safe_json_loads(profile.skills_json)
        if isinstance(skills_obj, list):
            skills_have = {str(x).strip().lower() for x in skills_obj if str(x).strip()}

    required = set(required_skills)
    matched = sorted(required & skills_have)
    missing = sorted(required - skills_have)

    # Skill component
    if not required:
        skills_score = 50.0  # neutral if JD doesn't mention tracked skills
    else:
        skills_score = (len(matched) / max(1, len(required))) * 100.0

    # Years component
    if min_years <= 0:
        years_score = 50.0
    else:
        years_score = min(1.0, years_have / max(min_years, 0.1)) * 100.0

    # Weighted rule score
    score = round((skills_score * 0.7) + (years_score * 0.3), 2)

    return RuleScore(
        score=score,
        details={
            "required_skills": sorted(required),
            "matched_skills": matched,
            "missing_skills": missing,
            "min_years": min_years,
            "years_have": years_have,
            "skills_score": round(skills_score, 2),
            "years_score": round(years_score, 2),
        },
    )


def combine_scores(*, embed_score: float, rules_score: float, w_embed: float = 0.7) -> float:
    w = max(0.0, min(1.0, float(w_embed)))
    total = (float(embed_score) * w) + (float(rules_score) * (1.0 - w))
    return round(max(0.0, min(100.0, total)), 2)
