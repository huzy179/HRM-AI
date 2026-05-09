from __future__ import annotations

import re
import unicodedata


_RE_WHITESPACE = re.compile(r"[ \t]+")
_RE_MANY_NEWLINES = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _RE_WHITESPACE.sub(" ", normalized)
    normalized = _RE_MANY_NEWLINES.sub("\n\n", normalized)
    return normalized.strip()
