from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.core.tenant import current_tenant_id


router = APIRouter()


class AuditEventOut(BaseModel):
    id: int
    ts: str
    subject: str
    ip: str
    method: str
    path: str
    status_code: int
    duration_ms: int
    request_id: str


@router.get("/events", response_model=List[AuditEventOut])
def list_audit_events(
    session: SessionDep,
    limit: int = 200,
    minutes: int = 60,
    path_prefix: str | None = None,
    subject_prefix: str | None = None,
) -> List[AuditEventOut]:
    limit = max(1, min(500, int(limit)))
    minutes = max(1, min(24 * 60, int(minutes)))

    since = datetime.utcnow() - timedelta(minutes=minutes)

    tenant_id = current_tenant_id()
    q = session.query(models.AuditEvent).filter(models.AuditEvent.ts >= since, models.AuditEvent.tenant_id == tenant_id)
    if path_prefix:
        q = q.filter(models.AuditEvent.path.like(f"{path_prefix}%"))
    if subject_prefix:
        q = q.filter(models.AuditEvent.subject.like(f"{subject_prefix}%"))

    rows = q.order_by(models.AuditEvent.id.desc()).limit(limit).all()
    return [
        AuditEventOut(
            id=r.id,
            ts=r.ts.isoformat(),
            subject=r.subject,
            ip=r.ip,
            method=r.method,
            path=r.path,
            status_code=int(r.status_code),
            duration_ms=int(r.duration_ms),
            request_id=str(getattr(r, "request_id", "") or ""),
        )
        for r in rows
    ]


@router.post("/purge")
def purge_audit_events(session: SessionDep, confirm: bool = False, days: int | None = None) -> dict:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to purge audit events")

    retention_days = int(os.environ.get("AUDIT_RETENTION_DAYS", "30") or "30")
    if days is not None:
        retention_days = int(days)
    retention_days = max(1, min(3650, retention_days))

    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    tenant_id = current_tenant_id()
    deleted = (
        session.query(models.AuditEvent)
        .filter(models.AuditEvent.ts < cutoff, models.AuditEvent.tenant_id == tenant_id)
        .delete()
    )
    session.commit()
    return {"ok": True, "deleted": int(deleted), "cutoff": cutoff.isoformat(), "retention_days": retention_days}
