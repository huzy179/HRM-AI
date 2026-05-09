from __future__ import annotations

import os
import uuid

from redis import Redis
from rq import Queue

from backend.db.session import SessionLocal
from backend.db import models


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def _redis() -> Redis:
    return Redis.from_url(REDIS_URL)


def enqueue_job(job_type: str, payload: dict) -> str:
    job_id = str(uuid.uuid4())

    session = SessionLocal()
    try:
        session.add(models.Job(id=job_id, job_type=job_type, status="QUEUED", progress=0))
        session.commit()
    finally:
        session.close()

    q = Queue("default", connection=_redis())
    q.enqueue("backend.worker.jobs.run_job", job_type, payload, job_id=job_id)
    return job_id

