from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from fastapi import Request, Response

from backend.api.rate_limit import enforce_rate_limit
from backend.api.security import AuthContext, get_auth_context, is_public_path
from backend.db.session import SessionLocal
from backend.db import models


async def auth_rate_limit_and_audit_middleware(request: Request, call_next: Callable) -> Response:
    start = time.time()

    ctx = AuthContext(subject="anonymous")
    if not is_public_path(request.url.path):
        ctx = get_auth_context(request)
        enforce_rate_limit(request, subject=ctx.subject)

    request.state.auth = ctx

    status_code = 500
    try:
        resp: Response = await call_next(request)
        status_code = resp.status_code
        return resp
    finally:
        # Best-effort audit log (don't break requests if DB is down)
        try:
            duration_ms = int(max(0.0, time.time() - start) * 1000)
            ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (
                request.client.host if request.client else "unknown"
            )
            session = SessionLocal()
            try:
                session.add(
                    models.AuditEvent(
                        ts=datetime.utcnow(),
                        subject=ctx.subject,
                        ip=ip,
                        method=request.method,
                        path=request.url.path,
                        status_code=int(status_code),
                        duration_ms=duration_ms,
                    )
                )
                session.commit()
            finally:
                session.close()
        except Exception:
            pass

