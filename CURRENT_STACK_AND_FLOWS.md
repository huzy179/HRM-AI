# HRM AI — Current stack & flows (2026-05-25)

Tài liệu này tóm tắt **toàn bộ công nghệ** và **luồng chạy hiện tại** của repo theo kiến trúc **API + Worker + UI**:

- CV screening: upload JD/CVs → parse/OCR → index (Chroma) → rank (embeddings + rules) → review (LLM) → trích xuất profile
- Policy chatbot (RAG): ingest tài liệu → chat có citations
- Offline-first: chạy local LLM qua **Ollama**

---

## 0) Quick start (Docker)

Yêu cầu: Docker Desktop.

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head

# Lần đầu: pull models
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3
```

- Streamlit UI: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

---

## 1) Tech stack

### 1.1 Runtime & packaging
- Python 3.10+
- Docker / Docker Compose (khuyến nghị để chạy đủ stack)
- `.venv` (dev local)

### 1.2 Backend / API
- FastAPI + Uvicorn
- Pydantic models (request/response)
- Upload handling: `python-multipart`
- Middleware (Phase 6): auth (API key), rate limit, audit log

### 1.3 Database & migrations
- SQLAlchemy 2
- Alembic migrations
- Postgres (Docker) cho stack đầy đủ
- SQLite dùng cho tests (contract tests)

### 1.4 Queue / Worker
- Redis
- RQ (Redis Queue)
- Worker processes lắng nghe nhiều queue bằng env `WORKER_QUEUES`
- Job status persisted ở DB table `jobs`
- Retry safety: chỉ retry khi job `FAILED/DONE` (không retry `RUNNING`), chặn retry job chưa “idempotent” nếu chưa có guard (có thể `force=true`).
- Lưu ý RQ: `Queue.enqueue()` có keyword arg reserved `job_id` (để set RQ job id) → DB job id được pass vào job function bằng positional arg, và RQ job id được set trùng DB job id để dùng chung.

### 1.5 AI / RAG
- Ollama (local)
  - Embeddings: `nomic-embed-text`
  - Chat/review: `llama3` (hoặc model khác qua env)
- LangChain integrations:
  - `langchain-ollama`
  - `langchain-chroma`
- Vector DB: ChromaDB (persist dưới `./data/chroma_db`)

### 1.6 Document processing / OCR
- PDF text extraction: PyMuPDF (`fitz`) + fallback `pdfplumber`
- OCR fallback: Tesseract + `pytesseract`
- OCR tunables qua env: `OCR_LANG`, `OCR_DPI`, `OCR_PSM`, `OCR_OEM`, `OCR_CROP_RATIO`
- OCR quality gate (heuristic) để chặn text OCR “rác”

### 1.7 Frontend
- Streamlit (UI gọi API)
- UI hỗ trợ API key (Phase 6) qua env `API_KEY`

### 1.8 Testing
- pytest
- requests
- fastapi TestClient (API contract tests)

---

## 2) Docker Compose services

### 2.1 Core services
- `ollama` (port `11434`): embeddings + chat
- `postgres` (port `5432`): DB
- `redis` (port `6379`): queue backend + (Phase 6) rate limit counters
- `api` (port `8000`): FastAPI
- `frontend` (port `8501`): Streamlit

### 2.2 Workers (queue split)
- `worker_parse`: nghe `parse,default`
- `worker_index`: nghe `index,default`
- `worker_llm`: nghe `llm,default`
- `worker` (legacy/all-in-one): nằm trong profile `legacy` để tránh chạy trùng
  - chạy khi cần: `docker compose --profile legacy up --build worker`

---

## 3) Queue mapping (job_type → queue)

- Queue `parse`
  - `parse_jd` (parse/OCR JD)
  - `parse_cvs` (parse/OCR CVs)
- Queue `index`
  - `screen_campaign` (index + rank)
  - `policy_ingest` (ingest policy docs)
  - `extract_profile` (extract CandidateProfile từ text)
  - `cleanup_storage` (tenant cleanup uploads/chroma)
  - `policy_clear`, `policy_rebuild`
- Queue `llm`
  - `review_candidate` (LLM review theo evidence chunks)
- Fallback queue `default`
  - job type không match mapping

---

## 4) Environment variables (quan trọng)

### 4.1 API / Worker / Frontend chung
- `DATABASE_URL`
  - Docker: `postgresql+psycopg://hrm:hrm@postgres:5432/hrm`
- `REDIS_URL`
  - Docker: `redis://redis:6379/0`

### 4.2 Ollama reliability
- `OLLAMA_BASE_URL` (Docker: `http://ollama:11434`)
- `OLLAMA_CHAT_MODEL` (default `llama3`)
- `OLLAMA_TIMEOUT_S` (default `60`)
- `OLLAMA_RETRIES` (default `2`)
- `OLLAMA_RETRY_BACKOFF_S` (default `1.0`)

### 4.3 OCR
- `OCR_LANG` (default `eng`, Docker thường set `vie+eng`)
- `OCR_DPI` (default `300`)
- `OCR_PSM` (default `6`)
- `OCR_OEM` (default `1`)
- `OCR_CROP_RATIO` (default `0.05`)
- (Windows local) `TESSERACT_CMD` (đường dẫn `tesseract.exe` nếu cần)

### 4.4 Upload limits (API protection)
- `MAX_UPLOAD_BYTES` (default `20MB`)
- `MAX_UPLOAD_FILES` (default `50`)
Ghi chú:
- Upload được ghi **streaming** xuống disk và enforce limit theo byte (không load toàn bộ vào RAM).

### 4.5 Worker runtime
- `WORKER_QUEUES` (ví dụ `parse,index,llm,default`)
- `LOG_LEVEL` (default `INFO`)

### 4.6 Phase 6: Auth + rate limit
- `HRM_API_KEYS` (comma-separated) hoặc `HRM_API_KEY` (single)
- `HRM_ADMIN_API_KEYS` hoặc `HRM_ADMIN_API_KEY` (admin-only endpoints)
- `RATE_LIMIT_PER_MIN` (default `120`)
- `RATE_LIMIT_AUTH_BONUS` (default `180`)
- Frontend: `API_KEY` để tự gửi header `X-API-Key`

### 4.7 Tenant + retention
- `TENANT_ID` (default `default`): namespace cho Chroma + DB scoping
- `AUDIT_RETENTION_DAYS` (default `30`): dùng bởi `POST /audit/purge`

---

## 5) Data model (DB tables) — high level

- `campaigns` (`tenant_id`)
- `campaign_settings` (`tenant_id`, `w_embed`, `required_skills_json`, `min_years_override`)
- `job_descriptions` (`tenant_id`, `text`, `parse_status`, `parse_method`, `error`)
- `candidates` (`tenant_id`, `text`, `parse_status`, `parse_method`, `error`, `parse_chars`, `quality_score`, `quality_reason`)
- `candidate_profiles` (`tenant_id`, …)
- `screening_results` (`tenant_id`, `score_embed`, `score_rules`, `score_total`, `evidence_json`, `rules_json`, `run_hash`)
- `review_results` (`tenant_id`, `score_llm`, `summary`, `strengths_json`, `gaps_json`, `evidence_json`)
- `policy_documents` (`tenant_id`, `text`, `ingest_status`, `ingest_method`, `error`)
- `jobs` (`tenant_id`, `status`, `progress`, `error`, `result_json`, `payload_json`, `attempt`, `parent_job_id`, `started_at`, `finished_at`, `duration_ms`)
- `audit_events` (`tenant_id`, `ts`, `subject`, `ip`, `method`, `path`, `status_code`, `duration_ms`, `request_id`)

---

## 6) API endpoints (hiện có)

### 6.1 Health (public)
- `GET /health`

### 6.2 Campaigns
- `POST /campaigns`
- `GET /campaigns`
- `GET /campaigns/{campaign_id}`

### 6.3 Campaign settings
- `GET /campaigns/{campaign_id}/settings` (auto-create default row)
- `PUT /campaigns/{campaign_id}/settings`
- `GET /campaigns/{campaign_id}/requirements`

### 6.4 JD / CVs
- `POST /campaigns/{campaign_id}/jd` (upload → enqueue `parse_jd`)
- `POST /campaigns/{campaign_id}/cvs` (upload multi → enqueue `parse_cvs`)
- `GET /campaigns/{campaign_id}/candidates`

### 6.5 Screening
- `POST /campaigns/{campaign_id}/screen` (enqueue `screen_campaign`)
- `GET /campaigns/{campaign_id}/ranking`

### 6.6 Review (LLM)
- `POST /campaigns/{campaign_id}/candidates/{candidate_id}/review` (enqueue `review_candidate`)
- `GET /campaigns/{campaign_id}/candidates/{candidate_id}/review`

### 6.7 Candidate profile
- `POST /campaigns/{campaign_id}/candidates/{candidate_id}/profile` (enqueue `extract_profile`)
- `GET /campaigns/{campaign_id}/candidates/{candidate_id}/profile`

### 6.8 Jobs
- `GET /jobs/{job_id}`
- `GET /jobs?limit=50` (tenant-scoped)
- `POST /jobs/{job_id}/retry?confirm=true` (admin key)
  - chỉ retry khi `FAILED/DONE`
  - chặn job_type chưa “idempotent” nếu chưa được allowlist (có thể `force=true`)

### 6.9 Policy RAG
- `POST /policy/ingest` (upload → enqueue `policy_ingest`)
- `GET /policy/documents`
- `POST /policy/chat`
- `POST /policy/clear?confirm=true` (admin key)
- `POST /policy/rebuild?confirm=true` (admin key)

### 6.10 Audit (Phase 6)
- `GET /audit/events` (admin key)
- `POST /audit/purge?confirm=true` (admin key)

### 6.11 Metrics
- `GET /metrics/summary?minutes=60`

### 6.12 Admin (Queue backlog & worker health)
- `GET /admin/queues` (admin key, Redis required)
- `GET /admin/workers` (admin key, Redis required)
- `POST /admin/cleanup?confirm=true&dry_run=true` (admin key, enqueue `cleanup_storage`)

---

## 7) End-to-end flows (chi tiết)

### 7.1 Campaign & JD parse/OCR
1) `POST /campaigns` → tạo campaign
2) `POST /campaigns/{id}/jd` → lưu file vào `uploads/tenant_<TENANT_ID>/campaign_<id>/jd/`, upsert `job_descriptions` (status `PENDING`)
3) Enqueue job `parse_jd` (queue `parse`)
4) Worker `parse_jd`:
   - Parse text: PyMuPDF → fallback pdfplumber → fallback OCR (Tesseract)
   - OCR quality gate: nếu text kém → `parse_status=ERROR`, `error=OCR_LOW_QUALITY:<reason>`
   - Save: `text/parse_status/parse_method/error`

### 7.2 CV upload + parse/OCR + quality metrics
1) `POST /campaigns/{id}/cvs` → lưu files vào `uploads/tenant_<TENANT_ID>/campaign_<id>/cvs/`, insert `candidates`
2) Enqueue job `parse_cvs` (queue `parse`)
3) Worker `parse_cvs`:
   - Idempotency: nếu candidate đã `OK` + có text → skip
   - Save parse fields + metrics: `parse_chars`, và nếu OCR thì set `quality_score/quality_reason`
   - Nếu OCR quality fail → set `parse_status=ERROR`, `error=OCR_LOW_QUALITY:<reason>`, xoá `text` để tránh rank/review

### 7.3 CandidateProfile extraction (rule-based)
1) `POST /campaigns/{id}/candidates/{candidate_id}/profile` → enqueue `extract_profile` (queue `index`)
2) Worker `extract_profile` → upsert `candidate_profiles`
3) `GET /campaigns/{id}/candidates/{candidate_id}/profile` → xem profile

### 7.4 Screening: index + composite rank
1) (optional) `PUT /campaigns/{id}/settings` để cấu hình `w_embed` + overrides
2) `POST /campaigns/{id}/screen` → enqueue `screen_campaign` (queue `index`)
3) Worker `screen_campaign`:
   - Validate JD (`JD_NOT_READY` nếu chưa OK)
   - Lọc candidates `parse_status == OK`
   - Index CV chunks vào Chroma theo campaign + tenant
     - Chroma path namespace: `./data/chroma_db/cv_screening/tenant_<TENANT_ID>/campaign_<id>/...`
   - Embedding rank → `score_embed`
   - Rule score (skills + years) từ `candidate_profiles` + override từ `campaign_settings` → `score_rules`
   - Combine: `score_total = w_embed*score_embed + (1-w_embed)*score_rules`
   - Save `screening_results` + `run_hash` (sha256) để idempotency
4) `GET /campaigns/{id}/ranking` → UI hiển thị bảng + drill-down evidence/rules

### 7.5 LLM Review (llama3) theo evidence chunks
1) `POST /campaigns/{id}/candidates/{candidate_id}/review` → enqueue `review_candidate` (queue `llm`)
2) Worker `review_candidate`:
   - Retrieve evidence chunks (top-N) từ Chroma
   - Call Ollama (format JSON) + retry/timeout wrapper
   - Save `review_results`
   - Idempotency: nếu đã có `review_results.summary` → skip
3) `GET /campaigns/{id}/candidates/{candidate_id}/review` → UI hiển thị

### 7.6 Policy RAG (ingest + chat)
1) `POST /policy/ingest` → lưu file vào `uploads/tenant_<TENANT_ID>/policy/`, insert `policy_documents`
2) Enqueue `policy_ingest` (queue `index`)
3) Worker `policy_ingest`:
   - Parse/OCR + quality gate
   - Chunk + index vào Chroma policy collection (tenant-scoped)
4) `POST /policy/chat`:
   - Retrieve top-k citations
   - Nếu không có citations → trả `"Không tìm thấy trong tài liệu"` (không gọi LLM)
   - Nếu có citations → call Ollama để sinh answer + trả citations

---

## 8) Streamlit pages (hiện có)

- `frontend/pages/0_Phase2_API.py`: API demo đơn giản
- `frontend/pages/2_CV_Screening_API.py`: CV screening (settings, parse/quality, ranking, review, profile)
- `frontend/pages/9_Policy_Chat_API.py`: policy ingest + chat (RAG)
- `frontend/pages/8_Admin_API.py`: admin (audit/events, purge, metrics/summary, policy docs, policy clear/rebuild, queues/workers)

