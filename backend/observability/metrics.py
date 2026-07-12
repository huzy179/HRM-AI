from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


HTTP_REQUESTS_TOTAL = Counter(
    "hrm_http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "hrm_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

JOBS_TOTAL = Gauge(
    "hrm_jobs_total",
    "Jobs created in the selected metrics window.",
    ["tenant_id", "status"],
)

JOB_TYPE_TOTAL = Gauge(
    "hrm_job_type_total",
    "Jobs by type in the selected metrics window.",
    ["tenant_id", "job_type", "status"],
)

JOB_DURATION_SECONDS = Gauge(
    "hrm_job_duration_seconds",
    "Job duration summary in seconds for completed jobs in the selected metrics window.",
    ["tenant_id", "job_type", "stat"],
)

RAG_CHAT_TOTAL = Counter(
    "hrm_rag_chat_total",
    "Policy RAG chat requests.",
    ["tenant_id", "status"],
)

RAG_RETRIEVED_CHUNKS = Histogram(
    "hrm_rag_retrieved_chunks",
    "Number of retrieved chunks for policy RAG requests.",
    ["tenant_id"],
    buckets=(0, 1, 2, 3, 5, 8, 13, 21),
)

RAG_CHAT_DURATION_SECONDS = Histogram(
    "hrm_rag_chat_duration_seconds",
    "Policy RAG chat duration in seconds.",
    ["tenant_id"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)

