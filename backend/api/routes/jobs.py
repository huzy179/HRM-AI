from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.core.tenant import current_tenant_id


router = APIRouter()


class JobOut(BaseModel):
    id: str
    job_type: str
    status: str
    progress: int
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int = 0


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, session: SessionDep) -> JobOut:
    tenant_id = current_tenant_id()
    job = session.get(models.Job, job_id)
    if job is None or getattr(job, "tenant_id", "default") != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        error=job.error,
        started_at=job.started_at.isoformat() if getattr(job, "started_at", None) else None,
        finished_at=job.finished_at.isoformat() if getattr(job, "finished_at", None) else None,
        duration_ms=int(getattr(job, "duration_ms", 0) or 0),
    )
