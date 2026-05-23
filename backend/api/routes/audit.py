from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models


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

    q = session.query(models.AuditEvent).filter(models.AuditEvent.ts >= since)
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
        )
        for r in rows
    ]

