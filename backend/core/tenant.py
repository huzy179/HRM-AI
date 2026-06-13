from __future__ import annotations

import os
from contextvars import ContextVar

_tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="default")


def set_current_tenant_id(tenant_id: str) -> None:
    _tenant_id_var.set(tenant_id)


def current_tenant_id() -> str:
    """
    Dynamic tenant ID resolved via request ContextVar, falling back to environment variable.
    """
    val = _tenant_id_var.get()
    if val != "default":
        return val
    return (os.environ.get("TENANT_ID") or "default").strip() or "default"

