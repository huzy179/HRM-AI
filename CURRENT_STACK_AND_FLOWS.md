# HRM AI — Current stack & flows (2026-05-23)

Tài liệu này tóm tắt **toàn bộ công nghệ** và **luồng chạy hiện tại** của repo (API + Worker + UI).

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
- Postgres (Docker) cho demo/stack đầy đủ
- SQLite dùng cho tests (contract tests)

### 1.4 Queue / Worker
- Redis
- RQ (Redis Queue)
- Worker processes lắng nghe nhiều queue bằng env `WORKER_QUEUES`
- Job status persisted ở DB table `jobs`

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
- UI có hỗ trợ API key (Phase 6) qua env `API_KEY`

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
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
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
- `RATE_LIMIT_PER_MIN` (default `120`)
- `RATE_LIMIT_AUTH_BONUS` (default `180`)
- Frontend: `API_KEY` để tự gửi header `X-API-Key`

---

## 5) Data model (DB tables) — high level

- `campaigns`
- `campaign_settings`
  - `w_embed` (0..1): trọng số embeddings trong `score_total`
  - `required_skills_json` (override skills, optional)
  - `min_years_override` (override years, optional)
- `job_descriptions`
  - `text`, `parse_status`, `parse_method`, `error`
- `candidates`
  - `text`, `parse_status`, `parse_method`, `error`
  - metrics: `parse_chars`, `quality_score`, `quality_reason`
- `candidate_profiles`
  - `name`, `email`, `phone`, `years_experience`, `education`, `skills_json`
- `screening_results`
  - `score_embed`, `score_rules`, `score_total`
  - `evidence_json` (top chunks)
  - `rules_json` (explain: required/matched/missing/min_years/years_have, …)
- `review_results`
  - `score_llm`, `summary`, `strengths_json`, `gaps_json`, `evidence_json`
- `policy_documents`
  - `text`, `ingest_status`, `ingest_method`, `error`
- `jobs`
  - `status`, `progress`, `error`
  - metrics: `started_at`, `finished_at`, `duration_ms`
- `audit_events` (Phase 6)
  - `ts, subject, ip, method, path, status_code, duration_ms`

---

## 6) API endpoints (hiện có)

### 6.1 Health (public)
- `GET /health`

### 6.2 Campaigns
- `POST /campaigns` (create)
- `GET /campaigns` (list)
- `GET /campaigns/{campaign_id}` (detail)

### 6.3 Campaign settings (Phase 5)
- `GET /campaigns/{campaign_id}/settings` (auto-create default row nếu chưa có)
- `PUT /campaigns/{campaign_id}/settings` (update config)
- `GET /campaigns/{campaign_id}/requirements`
  - đọc JD text và trả requirements sau khi áp override (nếu có)

### 6.4 JD / CVs
- `POST /campaigns/{campaign_id}/jd` (upload → enqueue `parse_jd`)
- `POST /campaigns/{campaign_id}/cvs` (upload nhiều file → enqueue `parse_cvs`)
- `GET /campaigns/{campaign_id}/candidates` (list + parse/quality fields)

### 6.5 Screening
- `POST /campaigns/{campaign_id}/screen` (enqueue `screen_campaign`)
- `GET /campaigns/{campaign_id}/ranking`
  - trả `score_total`, `score_embed`, `score_rules`, `evidence`, `rules`

### 6.6 Review (LLM)
- `POST /campaigns/{campaign_id}/candidates/{candidate_id}/review` (enqueue `review_candidate`)
- `GET /campaigns/{campaign_id}/candidates/{candidate_id}/review` (get saved review)

### 6.7 Candidate profile
- `POST /campaigns/{campaign_id}/candidates/{candidate_id}/profile` (enqueue `extract_profile`)
- `GET /campaigns/{campaign_id}/candidates/{candidate_id}/profile` (get profile)

### 6.8 Jobs
- `GET /jobs/{job_id}`
  - trả `status/progress/error` + `started_at/finished_at/duration_ms`

### 6.9 Policy RAG
- `POST /policy/ingest` (upload → enqueue `policy_ingest`)
- `POST /policy/chat` (retrieve + answer + citations)

> Lưu ý Phase 6: khi bật API key, mọi endpoint **trừ** `/health` cần header `X-API-Key`.

### 6.10 Audit (Phase 6)
- `GET /audit/events`
  - query params: `limit`, `minutes`, `path_prefix`, `subject_prefix`

---

## 7) End-to-end flows (chi tiết)

### 7.1 Campaign & JD parse/OCR
1) `POST /campaigns` → tạo campaign  
2) `POST /campaigns/{id}/jd` → lưu file vào `uploads/campaign_{id}/jd/`, upsert `job_descriptions` (status `PENDING`)  
3) Enqueue job `parse_jd` (queue `parse`)  
4) Worker `parse_jd`:
   - Parse text: PyMuPDF → fallback pdfplumber → fallback OCR (Tesseract)
   - OCR quality gate: nếu text kém → `parse_status=ERROR`, `error=OCR_LOW_QUALITY:<reason>`
   - Save: `text/parse_status/parse_method/error`

### 7.2 CV upload + parse/OCR + quality metrics
1) `POST /campaigns/{id}/cvs` → lưu files vào `uploads/campaign_{id}/cvs/`, insert `candidates`  
2) Enqueue job `parse_cvs` (queue `parse`)  
3) Worker `parse_cvs`:
   - Idempotency: nếu candidate đã `OK` + có text → skip
   - Save parse fields + metrics:
     - `parse_chars` (len text)
     - nếu OCR: set `quality_score/quality_reason`
   - Nếu OCR quality fail → set `parse_status=ERROR`, `error=OCR_LOW_QUALITY:<reason>`, xoá `text` để tránh rank/review

### 7.3 CandidateProfile extraction (rule-based)
1) `POST /campaigns/{id}/candidates/{candidate_id}/profile` → enqueue `extract_profile` (queue `index`)  
2) Worker `extract_profile`:
   - Extract rule-based: email/phone/years/skills keywords/education line
   - Upsert `candidate_profiles`
3) `GET /campaigns/{id}/candidates/{candidate_id}/profile` → xem profile

### 7.4 Screening: index + composite rank (Phase 5 ready)
1) (optional) `PUT /campaigns/{id}/settings` để cấu hình:
   - `w_embed` (0..1)
   - `required_skills` override (optional)
   - `min_years_override` (optional)
2) `POST /campaigns/{id}/screen` → enqueue `screen_campaign` (queue `index`)
3) Worker `screen_campaign`:
   - Validate JD (`JD_NOT_READY` nếu chưa OK)
   - Lọc candidates `parse_status == OK`
   - Index CV chunks vào Chroma theo campaign (`settings_for_campaign(campaign_id)`)
   - Embedding rank → `score_embed`
   - Rule score từ `candidate_profiles` (skills + years) + override từ `campaign_settings` → `score_rules`
   - Combine:
     - `score_total = w_embed*score_embed + (1-w_embed)*score_rules`
   - Save `screening_results`:
     - scores + `rules_json` (explain) + `evidence_json`
     - `run_hash` (sha256) để idempotency
4) `GET /campaigns/{id}/ranking` → UI hiển thị bảng + drill-down evidence/rules

### 7.5 LLM Review (llama3) theo evidence chunks
1) `POST /campaigns/{id}/candidates/{candidate_id}/review` → enqueue `review_candidate` (queue `llm`)
2) Worker `review_candidate`:
   - Evidence chunks từ Chroma (top-N)
   - Call Ollama (format JSON) + retry/timeout wrapper
   - Save `review_results`
   - Idempotency: nếu đã có `review_results.summary` → skip
3) `GET /campaigns/{id}/candidates/{candidate_id}/review` → UI hiển thị

### 7.6 Policy RAG (ingest + chat)
1) `POST /policy/ingest` → lưu file `uploads/policy/`, insert `policy_documents`  
2) Enqueue `policy_ingest` (queue `index`)  
3) Worker `policy_ingest`:
   - Parse/OCR + quality gate
   - Chunk + index vào Chroma policy collection
4) `POST /policy/chat`:
   - Retrieve top-k citations
   - Nếu không có citations → trả `"Không tìm thấy trong tài liệu"` (không gọi LLM)
   - Nếu có citations → call Ollama để sinh answer + trả citations

---

## 8) Phase 6 (Auth + Rate limit + Audit log) — behaviour

### 8.1 Auth (opt-in)
- Nếu không set `HRM_API_KEY(S)` → API chạy “open” (phù hợp LAN/demo).
- Nếu set `HRM_API_KEY(S)`:
  - mọi endpoint trừ `/health` yêu cầu `X-API-Key`
  - sai/missing key → `401`

### 8.2 Rate limit
- Fixed window per-minute theo `(ip, subject)`:
  - anonymous: `RATE_LIMIT_PER_MIN`
  - có key: `RATE_LIMIT_PER_MIN + RATE_LIMIT_AUTH_BONUS`
- Redis available → counter ở Redis
- Redis không available → fallback memory (theo process)

### 8.3 Audit log
- Middleware ghi best-effort vào `audit_events`
- Không làm fail request nếu DB down (silent fail)

---

## 9) Streamlit pages (hiện có)

- `frontend/pages/0_Phase2_API.py`: API demo đơn giản
- `frontend/pages/2_CV_Screening_API.py`:
  - campaign settings UI (w_embed + overrides)
  - candidates table (parse/quality)
  - ranking dashboard + filter + drill-down (Evidence/Rules/Review/Profile)
  - tự gửi `X-API-Key` nếu set env `API_KEY`
- `frontend/pages/9_Policy_Chat_API.py`: ingest policy + chat (tự gửi `X-API-Key` nếu set)
