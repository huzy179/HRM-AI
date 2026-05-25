from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.core.tenant import current_tenant_id
from backend.api.security import require_admin
from backend.worker.queue import enqueue_job


router = APIRouter()


class JobOut(BaseModel):
    id: str
    job_type: str
    attempt: int = 0
    parent_job_id: str = ""
    status: str
    progress: int
    error: str | None = None
    result: dict | list | str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int = 0


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, session: SessionDep) -> JobOut:
    tenant_id = current_tenant_id()
    job = session.get(models.Job, job_id)
    if job is None or getattr(job, "tenant_id", "default") != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")
    result = None
    raw = getattr(job, "result_json", "") or ""
    if raw:
        try:
            result = json.loads(raw)
        except Exception:
            result = raw

    return JobOut(
        id=job.id,
        job_type=job.job_type,
        attempt=int(getattr(job, "attempt", 0) or 0),
        parent_job_id=str(getattr(job, "parent_job_id", "") or ""),
        status=job.status,
        progress=job.progress,
        error=job.error,
        result=result,
        started_at=job.started_at.isoformat() if getattr(job, "started_at", None) else None,
        finished_at=job.finished_at.isoformat() if getattr(job, "finished_at", None) else None,
        duration_ms=int(getattr(job, "duration_ms", 0) or 0),
    )


@router.get("", response_model=list[JobOut])
def list_jobs(session: SessionDep, limit: int = 50) -> list[JobOut]:
    tenant_id = current_tenant_id()
    limit = max(1, min(200, int(limit)))
    rows = (
        session.query(models.Job)
        .filter(models.Job.tenant_id == tenant_id)
        .order_by(models.Job.created_at.desc())
        .limit(limit)
        .all()
    )
    out: list[JobOut] = []
    for job in rows:
        out.append(
            JobOut(
                id=job.id,
                job_type=job.job_type,
                attempt=int(getattr(job, "attempt", 0) or 0),
                parent_job_id=str(getattr(job, "parent_job_id", "") or ""),
                status=job.status,
                progress=job.progress,
                error=job.error,
                result=None,
                started_at=job.started_at.isoformat() if getattr(job, "started_at", None) else None,
                finished_at=job.finished_at.isoformat() if getattr(job, "finished_at", None) else None,
                duration_ms=int(getattr(job, "duration_ms", 0) or 0),
            )
        )
    return out


@router.post("/{job_id}/retry")
def retry_job(
    job_id: str,
    request: Request,
    session: SessionDep,
    confirm: bool = False,
    force: bool = False,
) -> dict:
    require_admin(request)
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to retry job")

    tenant_id = current_tenant_id()
    job = session.get(models.Job, job_id)
    if job is None or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")

    status = str(job.status or "")
    if status not in {"FAILED", "DONE"}:
        raise HTTPException(status_code=409, detail=f"Retry allowed only for FAILED/DONE (current={status})")

    # Safety: only allow retry for known-idempotent job types unless force=true
    idempotent_types = {
        "screen_campaign",  # guarded by run_hash
        "policy_rebuild",
        "policy_clear",
        "cleanup_storage",  # scoped + dry_run supported
        "extract_profile",  # upsert by candidate_id
        "review_candidate",  # idempotent (skip if already done)
        "policy_ingest",  # idempotent-ish (reingest OK docs safe)
        "parse_jd",  # has skip-if-already-ok
        "parse_cvs",  # has skip-if-already-ok
    }
    if (job.job_type not in idempotent_types) and not force:
        raise HTTPException(status_code=409, detail=f"Job type not marked idempotent: {job.job_type}. Use force=true to override.")

    payload_raw = getattr(job, "payload_json", "{}") or "{}"
    try:
        payload = json.loads(payload_raw)
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    new_attempt = int(getattr(job, "attempt", 0) or 0) + 1
    new_id = enqueue_job(
        job.job_type,
        payload,
        tenant_id=tenant_id,
        parent_job_id=job.id,
        attempt=new_attempt,
    )
    return {"ok": True, "job_id": new_id, "parent_job_id": job.id, "attempt": new_attempt}
