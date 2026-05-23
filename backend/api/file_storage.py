from __future__ import annotations

import re
import uuid
from pathlib import Path


_INVALID = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, *, max_len: int = 120) -> str:
    """
    Prevent path traversal and normalize to a filesystem-safe basename.
    Keeps extensions when possible.
    """
    base = Path(name or "file").name  # drop any path components
    base = base.strip().strip(".") or "file"
    base = _INVALID.sub("_", base)
    if len(base) > max_len:
        stem = Path(base).stem[: max_len - 10] or "file"
        suffix = Path(base).suffix[:10]
        base = f"{stem}{suffix}"
    return base


def unique_dest(dir_path: str | Path, original_name: str) -> Path:
    """
    Create a unique destination path under dir_path while preserving a safe basename.
    """
    d = Path(dir_path)
    d.mkdir(parents=True, exist_ok=True)
    safe = safe_filename(original_name)
    prefix = uuid.uuid4().hex[:8]
    return d / f"{prefix}__{safe}"

