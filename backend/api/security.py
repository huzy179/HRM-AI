from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Sequence

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class AuthContext:
    subject: str  # "api_key:<prefix>" | "anonymous"
    api_key_prefix: str | None = None
    role: str = "user"  # "user" | "admin"


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


def _parse_admin_api_keys() -> Sequence[str]:
    """
    Admin keys are optional. When provided, requests with an admin key get role=admin.
    Enable by setting either:
    - `HRM_ADMIN_API_KEYS` = comma-separated keys
    - `HRM_ADMIN_API_KEY`  = single key
    """
    keys_env = os.environ.get("HRM_ADMIN_API_KEYS", "").strip()
    if keys_env:
        return [k.strip() for k in keys_env.split(",") if k.strip()]
    single = os.environ.get("HRM_ADMIN_API_KEY", "").strip()
    if single:
        return [single]
    return []


def auth_enabled() -> bool:
    return bool(_parse_api_keys() or _parse_admin_api_keys())


def _mask_prefix(key: str) -> str:
    k = (key or "").strip()
    if len(k) <= 6:
        return k
    return k[:6]


def get_auth_context(request: Request) -> AuthContext:
    user_keys = list(_parse_api_keys())
    admin_keys = list(_parse_admin_api_keys())
    if not (user_keys or admin_keys):
        return AuthContext(subject="anonymous", api_key_prefix=None)

    provided = (request.headers.get("x-api-key") or "").strip()
    if not provided:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    role = "user"
    if provided in admin_keys:
        role = "admin"
    elif provided in user_keys:
        role = "user"
    else:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")

    prefix = _mask_prefix(provided)
    return AuthContext(subject=f"api_key:{prefix}", api_key_prefix=prefix, role=role)


def require_admin(request: Request) -> None:
    ctx = getattr(request.state, "auth", None)
    role = getattr(ctx, "role", "user") if ctx is not None else "user"
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")


def is_public_path(path: str) -> bool:
    # health endpoint is public for orchestration checks
    return path.rstrip("/") == "/health"
