from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from backend.api.rate_limit import enforce_rate_limit
from backend.api.security import AuthContext, get_auth_context, is_public_path
from backend.db import models
from backend.core.tenant import current_tenant_id


async def auth_rate_limit_and_audit_middleware(request: Request, call_next: Callable) -> Response:
    start = time.time()
    request_id = (request.headers.get("x-request-id") or "").strip() or str(uuid.uuid4())
    request.state.request_id = request_id
    tenant_id = current_tenant_id()
    request.state.tenant_id = tenant_id

    ctx = AuthContext(subject="anonymous")
    status_code = 500
    try:
        if not is_public_path(request.url.path):
            ctx = get_auth_context(request)
            enforce_rate_limit(request, subject=ctx.subject)
    except HTTPException as exc:
        status_code = int(exc.status_code)
        resp = JSONResponse(status_code=status_code, content={"detail": exc.detail})
        resp.headers["X-Request-Id"] = request_id
        resp.headers["X-Tenant-Id"] = tenant_id
        return resp

    request.state.auth = ctx

    try:
        resp: Response = await call_next(request)
        status_code = resp.status_code
        resp.headers["X-Request-Id"] = request_id
        resp.headers["X-Tenant-Id"] = tenant_id
        return resp
    finally:
        # Best-effort audit log (don't break requests if DB is down)
        try:
            duration_ms = int(max(0.0, time.time() - start) * 1000)
            ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (
                request.client.host if request.client else "unknown"
            )
            from backend.db.session import SessionLocal

            session = SessionLocal()
            try:
                session.add(
                    models.AuditEvent(
                        ts=datetime.utcnow(),
                        tenant_id=current_tenant_id(),
                        subject=ctx.subject,
                        ip=ip,
                        method=request.method,
                        path=request.url.path,
                        status_code=int(status_code),
                        duration_ms=duration_ms,
                        request_id=request_id,
                    )
                )
                session.commit()
            finally:
                session.close()
        except Exception:
            pass
