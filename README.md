# HRM AI — CV Screening + Policy RAG (Local LLM, Offline-first)

Repo này là một hệ thống HRM AI theo kiến trúc **API + Worker + UI**:

- CV screening: upload JD/CVs → parse/OCR → index (Chroma) → rank (embeddings) → review (LLM)  
- Policy chatbot (RAG): ingest tài liệu nội bộ → chat có citations  
- Offline-first: dùng **Ollama** chạy local

## Quick start (Docker)

Yêu cầu: Docker Desktop.

```bash
docker compose up --build
docker compose exec api alembic upgrade head

# lần đầu: pull models
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3
```

- Streamlit UI: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

## Tài liệu quan trọng

- `CURRENT_STACK_AND_FLOWS.md`: stack + endpoints + flows hiện tại
- `PHASE_6_RUNBOOK.md`: auth/rate-limit/audit/metrics

## Cấu hình (env vars)

Xem danh sách đầy đủ trong `CURRENT_STACK_AND_FLOWS.md`.

## Gợi ý chạy worker

Mặc định nên chạy tách queue:

- `worker_parse` (parse/OCR)
- `worker_index` (index/rank/ingest/profile)
- `worker_llm` (review)

Service `worker` (all-in-one) chỉ dùng khi bật profile legacy:

```bash
docker compose --profile legacy up --build worker
```

