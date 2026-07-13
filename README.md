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
- Policy Chatbot: `http://localhost:3000/policy-chat`
- Knowledge Base Admin: `http://localhost:3000/admin/knowledge-base`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (`admin` / `admin`)
- Loki: `http://localhost:3100`
- Jaeger traces: `http://localhost:16686`

## Tài liệu quan trọng

- `CURRENT_STACK_AND_FLOWS.md`: stack hiện tại, mục đích từng thành phần và flow sử dụng
- `Makefile`: các lệnh vận hành local thường dùng

## User test local

```text
admin / admin123
employee / user123
```

Tạo/cập nhật lại user test:

```bash
make seed-users
```

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

Policy RAG eval chạy trong app, không cần tạo venv riêng:

```bash
make policy-evals
```

Mở `http://localhost:3000/admin/evals`, bấm `Run Eval`, kết quả được lưu trong database và xử lý bởi worker.
