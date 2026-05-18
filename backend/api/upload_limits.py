from __future__ import annotations

import os

from fastapi import HTTPException, UploadFile


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


MAX_UPLOAD_BYTES = _env_int("MAX_UPLOAD_BYTES", 20 * 1024 * 1024)  # 20MB
MAX_UPLOAD_FILES = _env_int("MAX_UPLOAD_FILES", 50)


async def read_limited(upload: UploadFile) -> bytes:
    """
    Read UploadFile into memory but enforce max bytes.
    (Good enough for Phase 4; can be replaced with streaming later.)
    """
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_UPLOAD_BYTES} bytes): {upload.filename}",
        )
    return data


def ensure_file_count(files_count: int) -> None:
    if files_count > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=413, detail=f"Too many files (max {MAX_UPLOAD_FILES})")

