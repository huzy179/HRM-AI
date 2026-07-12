# HRM AI — CV Screening + Policy RAG (Local LLM, Offline-first)

Repo này là một hệ thống HRM AI theo kiến trúc **API + Worker + UI**:

- CV screening: upload JD/CVs → parse/OCR → index (Chroma) → rank (embeddings) → review (LLM)  
- Policy chatbot (RAG): ingest tài liệu nội bộ → chat có citations  
- Offline-first: dùng **Ollama** chạy local

## Quick start (Docker)

Yêu cầu: Docker Desktop.

```bash
make setup
```

- Next.js UI: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (`admin` / `admin`)
- Loki: `http://localhost:3100`
- Jaeger traces: `http://localhost:16686`

## Tài liệu quan trọng

- `CURRENT_STACK_AND_FLOWS.md`: stack hiện tại, mục đích từng thành phần và flow sử dụng
- `Makefile`: các lệnh vận hành local thường dùng

## Cấu hình (env vars)

Xem danh sách đầy đủ trong `CURRENT_STACK_AND_FLOWS.md`.

## Gợi ý chạy worker

Mặc định nên chạy tách queue:

- `worker_parse` (parse/OCR)
- `worker_index` (index/rank/ingest/profile)
- `worker_llm` (review)

Service `worker` (all-in-one) chỉ dùng khi bật profile legacy:

```bash
make legacy-worker
```

## Monitoring / Observability

- Prometheus scrape endpoint: `GET /metrics/prometheus`
- JSON summary endpoint cũ: `GET /metrics/summary`
- Grafana dashboard provisioned sẵn: `HRM AI Overview`
- Loki nhận log container qua Promtail
- OpenTelemetry traces được gửi sang Jaeger khi `OTEL_EXPORTER_OTLP_ENDPOINT` được set

Ragas Policy RAG eval (tách khỏi runtime image để Docker build nhẹ hơn):

```bash
python3 -m venv .venv-evals
. .venv-evals/bin/activate
pip install -r backend/requirements.txt -r evals/requirements.txt
python evals/ragas_policy_eval.py --input evals/policy_eval_questions.jsonl
```
