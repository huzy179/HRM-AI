# 📌 PHASE 2 Plan — Backend hóa + Async Pipeline + Policy RAG

**Ngày tạo:** 2026-05-10  
**Baseline hiện tại (Phase 1):** Streamlit UI + Parser (PDF/OCR) + Chroma + Ollama embeddings + llama3 review (top chunks) chạy Docker compose.

---

## 1) Mục tiêu Phase 2

- Chuẩn hoá hệ thống theo mô hình **Backend/API + Worker** (multi-user, có lưu trữ bền vững).
- CV Screening chạy **async** (OCR/index/rank/review không block UI).
- Lưu kết quả vào DB để **restart không mất dữ liệu**.
- Bổ sung **Policy Chatbot RAG** (ingest tài liệu nội bộ + chat có trích dẫn).

---

## 2) Kiến trúc đề xuất (Docker-first)

### Services
- `api` (FastAPI): nhận request, auth (basic), điều phối job, trả kết quả
- `worker` (RQ worker hoặc Celery): chạy OCR/parse/index/rank/LLM review/ingest policy
- `postgres`: lưu campaign, candidate, kết quả ranking & review, job status
- `redis`: queue + cache
- `ollama`: embeddings + llama3 chat
- `chroma_db` (volume): lưu vector theo campaign (CV/JD/policy)
- `frontend` (Streamlit): gọi API (không gọi trực tiếp module backend)

### Tech lựa chọn (khuyến nghị)
- Queue: **RQ + Redis** (đơn giản, đủ tốt cho Phase 2). *(Nếu cần scheduling/retry nâng cao có thể đổi Celery sau.)*
- DB: **Postgres + Alembic**
- API: **FastAPI**
- Vector DB: **Chroma (local volume)**
- LLM: **Ollama** (`nomic-embed-text` + `llama3`)

---

## 3) Data model tối thiểu (DB)

- `Campaign`: đợt tuyển dụng (name, created_at, status)
- `JobDescription`: 1 JD / campaign (file_path, text, created_at)
- `Candidate`: 1 CV / campaign (filename, file_path, text, parse_status, created_at)
- `ScreeningResult`: (campaign_id, candidate_id, score_embed, evidence_chunk_ids, created_at)
- `ReviewResult`: (campaign_id, candidate_id, score_llm, summary, strengths, gaps, raw_json, created_at)
- `PolicyDocument`: (file_path, text, ingested_at)
- `Job`: (job_id, type, status, progress, error, created_at, updated_at)

---

## 4) API scope (MVP Phase 2)

### 4.1 Campaign
- `POST /campaigns` tạo campaign
- `GET /campaigns` list
- `GET /campaigns/{id}` detail

### 4.2 JD
- `POST /campaigns/{id}/jd` upload JD (PDF/TXT) → lưu file + parse/OCR async
- `GET /campaigns/{id}/jd` lấy JD text/metadata

### 4.3 CV upload
- `POST /campaigns/{id}/cvs` upload nhiều CV (PDF) → lưu file + parse/OCR async
- `GET /campaigns/{id}/candidates` list candidates + parse status

### 4.4 Screening async
- `POST /campaigns/{id}/screen` enqueue job index+rank
- `GET /campaigns/{id}/ranking` trả ranking

### 4.5 LLM review (llama3)
- `POST /campaigns/{id}/candidates/{candidate_id}/review` enqueue review
- `GET /campaigns/{id}/candidates/{candidate_id}/review` lấy review

### 4.6 Job status
- `GET /jobs/{job_id}` (status/progress/error)

### 4.7 Policy RAG
- `POST /policy/ingest` upload nhiều file policy (PDF/TXT) → ingest async
- `POST /policy/chat` query → trả answer + citations (source chunks)

---

## 5) Pipeline xử lý (worker)

### 5.1 Parse/OCR
- Input: JD/CV PDF
- Output: text + parse_status

### 5.2 Chunk + Index (Chroma)
- CV: chunk theo `CV_CHUNK_SIZE/OVERLAP`, metadata `{campaign_id, candidate_id, chunk_id}`
- JD: store text (chưa cần index như doc)
- Policy: chunk theo config riêng, metadata `{doc_id, chunk_id, source}`

### 5.3 Rank
- Query = JD text → `similarity_search_with_score(k)`
- Gom theo `candidate_id` lấy max score (giống Phase 1)
- Lưu `ScreeningResult`

### 5.4 Review (LLM)
- Lấy top evidence chunks theo candidate_id → llama3 trả JSON
- Lưu `ReviewResult`

---

## 6) Timeline (3 tuần, có checkpoint)

### Tuần 1 — Backend + DB + Upload
- [ ] Scaffold FastAPI app (`backend/api`, `backend/main.py`)
- [ ] Postgres + Alembic migrations
- [ ] DB models + CRUD cơ bản
- [ ] Upload JD/CV (lưu file + record DB)
- [ ] Endpoint `jobs/{id}` (stub)

### Tuần 2 — Worker + Screening async
- [ ] Redis + RQ worker
- [ ] Jobs: parse/OCR JD/CV
- [ ] Jobs: index CV vào Chroma theo campaign
- [ ] Jobs: rank candidates theo JD
- [ ] API: trigger screen + get ranking
- [ ] Streamlit chuyển sang gọi API cho flow screening

### Tuần 3 — LLM review + Policy RAG + Hardening
- [ ] Jobs: llama3 review theo evidence chunks
- [ ] Policy ingest + Policy chat endpoint (answer + citations)
- [ ] Logging + retry/timeouts (Ollama calls)
- [ ] Integration tests (API + worker happy path)
- [ ] `PHASE_2_RESULTS.md` (report)

---

## 7) Acceptance Criteria Phase 2

- [ ] Upload CV/JD qua API; worker parse/OCR chạy async, UI không bị block
- [ ] Ranking có thể lấy lại sau restart containers (DB + chroma volume)
- [ ] Review llama3 chạy theo request, trả JSON chuẩn và lưu DB
- [ ] Policy chatbot trả answer có citations (trích nguồn chunk)
- [ ] Có runbook chạy Docker compose + migrate DB + run worker

---

## 8) Decisions cần chốt trước khi code Phase 2

1) Queue: giữ **RQ** (khuyến nghị) hay dùng **Celery**?
2) Auth: cần login nội bộ (basic) hay để mở trong LAN?
3) UI: giữ Streamlit (nhanh) hay chuyển React/Next?

