# Phase 6 Runbook — Auth (API key) + Rate limit + Audit log + Metrics

## 1) Bật API key (opt-in)

Auth chỉ bật khi service `api` có set một trong các env:

- `HRM_API_KEYS` (comma-separated), ví dụ: `dev_key_123,dev_key_456`
- hoặc `HRM_API_KEY` (single key)

Khi bật auth, client phải gửi header:

- `X-API-Key: <key>`

`GET /health` vẫn public.

## 2) Cấu hình rate limit

- `RATE_LIMIT_PER_MIN` (default 120): giới hạn request/phút theo `(ip, subject)`
- `RATE_LIMIT_AUTH_BONUS` (default 180): cộng thêm quota nếu có API key

Ưu tiên dùng Redis nếu có `REDIS_URL`, fallback memory nếu không.

## 3) Audit log

Middleware ghi best-effort vào table `audit_events`:

- `ts, subject, ip, method, path, status_code, duration_ms, request_id`

## 4) Docker compose gợi ý

- Set trong `api`:
  - `HRM_API_KEYS=dev_key_123`
- Set trong `frontend`:
  - `API_KEY=dev_key_123`

## 5) DB migration

Chạy:

```bash
docker compose exec api alembic upgrade head
```

## 6) Audit endpoint

Xem audit events:

- `GET /audit/events?minutes=60&limit=200`

## 7) Metrics endpoint

- `GET /metrics/summary?minutes=60`

## 8) Phase 7: Policy index hygiene

- Clear policy index (tenant-scoped):
  - `POST /policy/clear?confirm=true`
- Rebuild policy index từ `policy_documents` đã ingest OK:
  - `POST /policy/rebuild?confirm=true`

