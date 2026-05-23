from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.core.tenant import current_tenant_id


router = APIRouter()


class JobTypeStats(BaseModel):
    job_type: str
    count: int
    avg_duration_ms: int
    p95_duration_ms: int
    failed: int


class MetricsOut(BaseModel):
    window_minutes: int
    jobs_total: int
    jobs_done: int
    jobs_failed: int
    by_type: List[JobTypeStats]


@router.get("/summary", response_model=MetricsOut)
def metrics_summary(session: SessionDep, minutes: int = 60, max_rows: int = 5000) -> MetricsOut:
    minutes = max(1, min(24 * 60, int(minutes)))
    max_rows = max(100, min(20000, int(max_rows)))
    since = datetime.utcnow() - timedelta(minutes=minutes)

    tenant_id = current_tenant_id()
    rows = (
        session.query(models.Job)
        .filter(models.Job.created_at >= since, models.Job.tenant_id == tenant_id)
        .order_by(models.Job.created_at.desc())
        .limit(max_rows)
        .all()
    )

    total = len(rows)
    done = sum(1 for r in rows if r.status == "DONE")
    failed = sum(1 for r in rows if r.status == "FAILED")

    groups: Dict[str, list[models.Job]] = {}
    for r in rows:
        groups.setdefault(r.job_type, []).append(r)

    by_type: List[JobTypeStats] = []
    for job_type, items in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0])):
        durations = sorted([int(getattr(x, "duration_ms", 0) or 0) for x in items if (getattr(x, "duration_ms", 0) or 0) > 0])
        avg = int(sum(durations) / len(durations)) if durations else 0
        p95 = 0
        if durations:
            idx = int(round(0.95 * (len(durations) - 1)))
            p95 = int(durations[idx])
        failed_count = sum(1 for x in items if x.status == "FAILED")
        by_type.append(
            JobTypeStats(
                job_type=job_type,
                count=len(items),
                avg_duration_ms=avg,
                p95_duration_ms=p95,
                failed=failed_count,
            )
        )

    return MetricsOut(
        window_minutes=minutes,
        jobs_total=total,
        jobs_done=done,
        jobs_failed=failed,
        by_type=by_type,
    )
