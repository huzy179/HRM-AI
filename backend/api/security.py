from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Sequence

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class AuthContext:
    subject: str  # "api_key:<prefix>" | "anonymous"
    api_key_prefix: str | None = None


def _parse_api_keys() -> Sequence[str]:
    """
    Enable auth by setting either:
    - `HRM_API_KEYS` = comma-separated keys
    - `HRM_API_KEY`  = single key
    """
    keys_env = os.environ.get("HRM_API_KEYS", "").strip()
    if keys_env:
        return [k.strip() for k in keys_env.split(",") if k.strip()]
    single = os.environ.get("HRM_API_KEY", "").strip()
    if single:
        return [single]
    return []


def auth_enabled() -> bool:
    return bool(_parse_api_keys())


def _mask_prefix(key: str) -> str:
    k = (key or "").strip()
    if len(k) <= 6:
        return k
    return k[:6]


def get_auth_context(request: Request) -> AuthContext:
    keys = _parse_api_keys()
    if not keys:
        return AuthContext(subject="anonymous", api_key_prefix=None)

    provided = (request.headers.get("x-api-key") or "").strip()
    if not provided:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    if provided not in keys:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")

    prefix = _mask_prefix(provided)
    return AuthContext(subject=f"api_key:{prefix}", api_key_prefix=prefix)


def is_public_path(path: str) -> bool:
    # health endpoint is public for orchestration checks
    return path.rstrip("/") == "/health"

