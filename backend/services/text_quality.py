from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextQuality:
    ok: bool
    score: float  # 0..1
    reason: str = ""
    chars: int = 0
    alpha_ratio: float = 0.0
    weird_ratio: float = 0.0


def assess_text_quality(text: str) -> TextQuality:
    """
    Heuristic quality gate to detect garbage OCR outputs.
    This is language-agnostic and intentionally simple.
    """
    t = (text or "").strip()
    chars = len(t)
    if chars == 0:
        return TextQuality(ok=False, score=0.0, reason="EMPTY_TEXT", chars=0)

    alpha = 0
    digits = 0
    spaces = 0
    weird = 0
    for ch in t:
        if ch.isalpha():
            alpha += 1
        elif ch.isdigit():
            digits += 1
        elif ch.isspace():
            spaces += 1
        else:
            # punctuation/symbols/unknown
            weird += 1

    denom = max(chars, 1)
    alpha_ratio = alpha / denom
    weird_ratio = weird / denom

    # score is a soft metric: prefer texts with decent alphabetic content and low garbage symbols
    score = max(0.0, min(1.0, (alpha_ratio * 1.2) - (weird_ratio * 1.5)))

    # Hard gates (tuned for CV-sized docs)
    if chars < 200:
        return TextQuality(
            ok=False,
            score=score,
            reason="TOO_SHORT",
            chars=chars,
            alpha_ratio=alpha_ratio,
            weird_ratio=weird_ratio,
        )
    if alpha_ratio < 0.35:
        return TextQuality(
            ok=False,
            score=score,
            reason="LOW_ALPHA_RATIO",
            chars=chars,
            alpha_ratio=alpha_ratio,
            weird_ratio=weird_ratio,
        )
    if weird_ratio > 0.25:
        return TextQuality(
            ok=False,
            score=score,
            reason="HIGH_GARBAGE_RATIO",
            chars=chars,
            alpha_ratio=alpha_ratio,
            weird_ratio=weird_ratio,
        )

    return TextQuality(ok=True, score=score, chars=chars, alpha_ratio=alpha_ratio, weird_ratio=weird_ratio)

