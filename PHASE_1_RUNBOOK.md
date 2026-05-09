# Phase 1 Runbook — CV Screening (Docker-first)

## 1) Prerequisites

- Docker Desktop (Windows)

## 2) Start stack

```bash
docker compose up --build
```

Mở UI: `http://localhost:8501`

## 3) Pull models (lần đầu)

Embeddings (bắt buộc):

```bash
docker compose exec ollama ollama pull nomic-embed-text
```

LLM review (tuỳ chọn nhưng khuyến nghị):

```bash
docker compose exec ollama ollama pull llama3
```

## 4) Chuẩn bị dữ liệu

- CV PDFs: bỏ vào `data/raw_cv/` (không commit CV thật)
- JD: có thể upload PDF/TXT trên UI hoặc dùng mẫu trong `data/sample_jd/`

Lưu ý:
- Nếu CV/JD là PDF scan (ảnh) thì cần OCR. Docker image đã có Tesseract.

## 5) Cách dùng trên UI

1. Vào sidebar → Pages → `1_CV_Screening`
2. Nhập JD (hoặc upload JD PDF)
3. Upload CV PDFs (hoặc tick “dùng PDF trong `data/raw_cv/`”)
4. Bấm `Run screening`
5. Chọn 1 CV → bấm `Generate review (llama3)` để xem review

## 6) Run tests

```bash
docker compose exec app pytest -q
```

## 7) Stop stack

```bash
docker compose down
```

