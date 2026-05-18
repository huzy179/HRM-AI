# Phase 3 Plan — Hardening + RAG/LLM Reliability

**Ngày tạo:** 2026-05-18

## Mục tiêu

- Làm hệ thống ổn định hơn khi chạy demo/production-lite: timeout/retry/logging rõ ràng.
- Giảm lỗi ngẫu nhiên khi gọi Ollama (network/latency) và tăng khả năng debug.
- Bổ sung E2E tests có điều kiện (skip nếu Ollama không chạy).

## Checklist triển khai

### 0) Queue tách lớp (khuyến nghị)
- Route job theo queue:
  - `parse`: `parse_jd`, `parse_cvs`
  - `index`: `screen_campaign`, `policy_ingest`
  - `llm`: `review_candidate`
- Worker lắng nghe nhiều queue qua env `WORKER_QUEUES=parse,index,llm,default`.

### 1) Reliability (Ollama)
- Thêm env vars:
  - `OLLAMA_TIMEOUT_S` (default 60)
  - `OLLAMA_RETRIES` (default 2)
  - `OLLAMA_RETRY_BACKOFF_S` (default 1.0)
- Áp dụng `client_kwargs={"timeout": ...}` cho:
  - `ChatOllama` (review + policy answer)
  - `OllamaEmbeddings` (policy retrieval/index)
- Wrapper retry cho `llm.invoke(...)` (bounded, backoff).

### 2) Worker logging
- `run_worker.py` cấu hình `logging.basicConfig(...)`.
- `jobs.py` log `job.start/job.done/job.failed` kèm `duration_s`.

### 3) Policy RAG guardrail
- Nếu retrieve không có citations → trả `Không tìm thấy trong tài liệu` (không gọi LLM).

### 4) Tests
- Thêm `tests/test_policy_rag_e2e.py` (skip nếu Ollama không sẵn sàng).
