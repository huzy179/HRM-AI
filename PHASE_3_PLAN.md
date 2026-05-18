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
- (Tuỳ chọn, khuyến nghị cho demo ổn định) Tách nhiều worker service để scale độc lập:
  - `worker_parse` nghe `parse,default`
  - `worker_index` nghe `index,default`
  - `worker_llm` nghe `llm,default`
- Tránh chạy trùng: service `worker` (all-in-one) được đặt trong profile `legacy` và chỉ chạy khi:
  - `docker compose --profile legacy up --build worker`

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
- Thêm API contract tests (sqlite + mock queue):
  - `tests/test_api_contract.py`

### 5) Upload limits (API)
- Env vars:
  - `MAX_UPLOAD_BYTES` (default 20MB)
  - `MAX_UPLOAD_FILES` (default 50)
- Áp dụng cho:
  - `POST /campaigns/{id}/jd`
  - `POST /campaigns/{id}/cvs`
  - `POST /policy/ingest`

### 6) Text quality gate (OCR)
- Nếu `parse_method` là `ocr_*` và text bị đánh giá rác → set status `ERROR`, error `OCR_LOW_QUALITY:<reason>`.
- Candidates có metrics:
  - `parse_chars`, `quality_score`, `quality_reason`

## Ghi chú môi trường dev

- API upload dùng `python-multipart` (đã có trong `backend/requirements.txt`).
