from __future__ import annotations

import os
import uuid

from typing import Any

from backend.db.session import SessionLocal
from backend.db import models
from backend.core.tenant import current_tenant_id


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

QUEUE_PARSE = "parse"
QUEUE_INDEX = "index"
QUEUE_LLM = "llm"
QUEUE_DEFAULT = "default"

JOB_TYPE_TO_QUEUE: dict[str, str] = {
    # Parse/OCR
    "parse_jd": QUEUE_PARSE,
    "parse_cvs": QUEUE_PARSE,
    # Index/rank (embedding + chroma)
    "screen_campaign": QUEUE_INDEX,
    "policy_ingest": QUEUE_INDEX,
    "policy_rebuild": QUEUE_INDEX,
    "policy_clear": QUEUE_INDEX,
    "extract_profile": QUEUE_INDEX,
    # LLM calls
    "review_candidate": QUEUE_LLM,
}


def _redis() -> Any:
    from redis import Redis

    return Redis.from_url(REDIS_URL)


def queue_for_job_type(job_type: str) -> str:
    return JOB_TYPE_TO_QUEUE.get(job_type, QUEUE_DEFAULT)


def enqueue_job(job_type: str, payload: dict) -> str:
    job_id = str(uuid.uuid4())
    tenant_id = current_tenant_id()

    session = SessionLocal()
    try:
        session.add(models.Job(id=job_id, tenant_id=tenant_id, job_type=job_type, status="QUEUED", progress=0))
        session.commit()
    finally:
        session.close()

    from rq import Queue

    q = Queue(queue_for_job_type(job_type), connection=_redis())
    q.enqueue("backend.worker.jobs.run_job", job_type, payload, job_id=job_id)
    return job_id
