from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request

from backend.api.security import require_admin
from backend.worker.queue import enqueue_job


router = APIRouter()


@router.post("/cleanup")
def cleanup_storage(request: Request, confirm: bool = False, dry_run: bool = True) -> dict:
    require_admin(request)
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to run cleanup")
    job_id = enqueue_job("cleanup_storage", {"dry_run": bool(dry_run)})
    return {"ok": True, "job_id": job_id, "dry_run": bool(dry_run)}


@router.get("/queues")
def queue_backlog(request: Request) -> dict:
    require_admin(request)
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        raise HTTPException(status_code=503, detail="REDIS_URL not set")
    try:
        from redis import Redis
        from rq import Queue
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Missing deps: {exc.__class__.__name__}") from exc

    conn = Redis.from_url(redis_url)
    names = ["parse", "index", "llm", "default"]
    data = {}
    for name in names:
        q = Queue(name, connection=conn)
        data[name] = {
            "count": int(q.count),
            "failed_count": int(getattr(q, "failed_job_registry", None).count if getattr(q, "failed_job_registry", None) else 0),
            "started_count": int(getattr(q, "started_job_registry", None).count if getattr(q, "started_job_registry", None) else 0),
            "deferred_count": int(getattr(q, "deferred_job_registry", None).count if getattr(q, "deferred_job_registry", None) else 0),
            "scheduled_count": int(getattr(q, "scheduled_job_registry", None).count if getattr(q, "scheduled_job_registry", None) else 0),
        }
    return {"ok": True, "queues": data}


@router.get("/workers")
def worker_health(request: Request) -> dict:
    require_admin(request)
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        raise HTTPException(status_code=503, detail="REDIS_URL not set")
    try:
        from redis import Redis
        from rq import Worker
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Missing deps: {exc.__class__.__name__}") from exc

    conn = Redis.from_url(redis_url)
    workers = Worker.all(connection=conn)
    out = []
    for w in workers:
        out.append(
            {
                "name": getattr(w, "name", ""),
                "hostname": getattr(w, "hostname", ""),
                "pid": getattr(w, "pid", None),
                "state": str(getattr(w, "get_state", lambda: "")()),
                "queues": [getattr(q, "name", str(q)) for q in getattr(w, "queues", [])],
                "last_heartbeat": getattr(w, "last_heartbeat", None).isoformat() if getattr(w, "last_heartbeat", None) else None,
                "birth_date": getattr(w, "birth_date", None).isoformat() if getattr(w, "birth_date", None) else None,
            }
        )
    return {"ok": True, "workers": out}
