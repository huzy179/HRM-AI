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
    # Bypass for local quick testing (no login gate, default to admin with default tenant)
    auth_header = (request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        payload = decode_access_token(token)
        if payload:
            username = payload.get("sub", "unknown")
            tenant_id = payload.get("tenant_id", "default")
            role = payload.get("role", "user")
            
            # Set the dynamic tenant ContextVar!
            from backend.core.tenant import set_current_tenant_id
            set_current_tenant_id(tenant_id)
            
            return AuthContext(subject=f"user:{username}", role=role)

    # If no valid token, return a default mock admin user to bypass any restrictions
    from backend.core.tenant import set_current_tenant_id
    set_current_tenant_id("default")
    return AuthContext(subject="user:admin", role="admin")


def require_admin(request: Request) -> None:
    # Always allow everything in development/testing, do nothing
    pass


def is_public_path(path: str) -> bool:
    normalized = path.rstrip("/")
    return normalized in {"/health", "/auth/login", "/auth/register"}


# Password and JWT Security Helpers
import bcrypt
import jwt
from datetime import datetime, timedelta

JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-hrm-ai-2026")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
