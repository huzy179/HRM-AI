# Phase 2 Runbook — API + Worker + Postgres + Redis + Ollama

## Start stack

```bash
docker compose up --build
```

> Gợi ý: nếu muốn scale theo loại job, có thể chạy thêm các worker chuyên biệt:
> - `docker compose up --build worker_parse worker_index worker_llm`
> (service `worker` (legacy, nghe tất cả queue) chỉ chạy khi bật profile: `docker compose --profile legacy up --build worker`)

## Run migrations

```bash
docker compose exec api alembic upgrade head
```

## Pull models (lần đầu)

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3
```

## URLs

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`

## Phase 2 demo flows

### CV screening (API)

1. Mở Streamlit → page `0_Phase2_API`
2. Create campaign
3. Upload JD (PDF/TXT) → nhận `job_id`
4. Upload CVs (PDF) → nhận `job_id`
5. Start screening → nhận `job_id`
6. Check job status bằng `/jobs/{job_id}`
7. Xem ranking bằng `/campaigns/{id}/ranking`

### LLM review (API)

- Gọi `POST /campaigns/{id}/candidates/{candidate_id}/review` → lấy `job_id`
- Lấy review: `GET /campaigns/{id}/candidates/{candidate_id}/review`

### Policy RAG

1. Mở Streamlit → page `9_Policy_Chat_API`
2. Upload policy docs → ingest
3. Ask question → nhận answer + citations

## Stop

```bash
docker compose down
```
