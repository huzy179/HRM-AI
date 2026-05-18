from __future__ import annotations

from backend.worker.queue import QUEUE_DEFAULT, QUEUE_INDEX, QUEUE_LLM, QUEUE_PARSE, queue_for_job_type


def test_queue_for_job_type_known() -> None:
    assert queue_for_job_type("parse_jd") == QUEUE_PARSE
    assert queue_for_job_type("parse_cvs") == QUEUE_PARSE
    assert queue_for_job_type("screen_campaign") == QUEUE_INDEX
    assert queue_for_job_type("policy_ingest") == QUEUE_INDEX
    assert queue_for_job_type("extract_profile") == QUEUE_INDEX
    assert queue_for_job_type("review_candidate") == QUEUE_LLM


def test_queue_for_job_type_unknown_defaults() -> None:
    assert queue_for_job_type("unknown_job_type") == QUEUE_DEFAULT
