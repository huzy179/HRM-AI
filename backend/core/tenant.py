from __future__ import annotations

import os


def current_tenant_id() -> str:
    """
    Deployment-scoped tenant id.
    For now, tenant is determined by env TENANT_ID.
    """
    return (os.environ.get("TENANT_ID") or "default").strip() or "default"

