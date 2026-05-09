from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models


router = APIRouter()


class JobOut(BaseModel):
    id: str
    job_type: str
    status: str
    progress: int
    error: str | None = None


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, session: SessionDep) -> JobOut:
    job = session.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        error=job.error,
    )

