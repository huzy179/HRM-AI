from __future__ import annotations

import os
import uuid
import json

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
    "policy_eval": QUEUE_INDEX,
    "cleanup_storage": QUEUE_INDEX,
    "extract_profile": QUEUE_INDEX,
    # LLM calls
    "review_candidate": QUEUE_LLM,
}


def _redis() -> Any:
    from redis import Redis

    return Redis.from_url(REDIS_URL)


def queue_for_job_type(job_type: str) -> str:
    return JOB_TYPE_TO_QUEUE.get(job_type, QUEUE_DEFAULT)


def enqueue_job(
    job_type: str,
    payload: dict,
    *,
    tenant_id: str | None = None,
    parent_job_id: str = "",
    attempt: int = 0,
) -> str:
    job_id = str(uuid.uuid4())
    tenant = (tenant_id or current_tenant_id()).strip() or "default"

    session = SessionLocal()
    try:
        session.add(
            models.Job(
                id=job_id,
                tenant_id=tenant,
                job_type=job_type,
                payload_json=json.dumps(payload or {}, ensure_ascii=False),
                parent_job_id=parent_job_id or "",
                attempt=int(attempt or 0),
                status="QUEUED",
                progress=0,
            )
        )
        session.commit()
    finally:
        session.close()

    from rq import Queue

    q = Queue(queue_for_job_type(job_type), connection=_redis())
    # NOTE: RQ's Queue.enqueue() has a reserved kwarg named `job_id` (to set the RQ job id),
    # so we must NOT use `job_id=...` to pass an argument to our job function.
    # We pass our DB job_id as a positional arg (3rd arg), and also set the RQ job id to match.
    q.enqueue("backend.worker.jobs.run_job", job_type, payload, job_id, job_id=job_id)
    return job_id
