from __future__ import annotations

import os
from pathlib import Path

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


async def save_upload_limited(upload: UploadFile, dest: str | Path) -> int:
    """
    Stream UploadFile to disk with max-bytes enforcement.
    Returns total bytes written.
    """
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with path.open("wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                try:
                    f.close()
                finally:
                    try:
                        if path.exists():
                            path.unlink()
                    except Exception:
                        pass
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large (max {MAX_UPLOAD_BYTES} bytes): {upload.filename}",
                )
            f.write(chunk)
    return total


def ensure_file_count(files_count: int) -> None:
    if files_count > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=413, detail=f"Too many files (max {MAX_UPLOAD_FILES})")
