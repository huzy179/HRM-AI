# ✅ Phase 1 Tasks — CV Screening (Ollama Embeddings + LangChain + Chroma)

**Mục tiêu Phase 1:** Upload CV (PDF) + nhập Job Description → parse text → index vào Chroma → semantic matching bằng **Ollama embeddings** → chấm điểm & xếp hạng trên Streamlit.

**Thời gian dự kiến:** 10–14 ngày (2 tuần)  
**Last updated:** 2026-05-09

---

## 0) Definition of Done (DoD)

Phase 1 được xem là hoàn thành khi:

- [ ] Chạy được end-to-end trên máy local (Windows) theo 1 hướng dẫn duy nhất.
- [ ] Parse được text từ PDF cho đa số CV mẫu (>= 90% file test đọc được text; file lỗi có log/hiển thị lỗi).
- [ ] Index CV vào Chroma và query JD ra ranking (score 0–100).
- [ ] Streamlit UI: upload nhiều CV + nhập JD + xem bảng ranking + xem chi tiết 1 CV.
- [ ] Có unit tests tối thiểu cho parser/matcher và 1 e2e test đơn giản.
- [ ] Có tài liệu: cách cài Ollama, pull model, cách chạy.

---

## 1) Chuẩn bị & quy ước (Day 1)

### 1.1. Môi trường
- [x] Chuẩn bị Docker (`Dockerfile`, `docker-compose.yml`)
- [ ] Cài Docker Desktop (Windows)
- [ ] Build & chạy stack:
  - [ ] `docker compose up --build`
- [ ] Pull embeddings model trong Ollama container:
  - [ ] `docker compose exec ollama ollama pull nomic-embed-text`
- [x] Chuẩn bị dependencies Python (`backend/requirements.txt`) (dùng cho Docker build)

### 1.2. Quy ước đường dẫn dữ liệu (local)
- [x] CV test để ở `data/raw_cv/` (đã tạo thư mục + `.gitkeep`)
- [x] JD mẫu để ở `data/sample_jd/` (đã thêm 2 file JD mẫu)
- [x] Chroma persist ở `data/chroma_db/cv_screening/` (đã tạo `data/chroma_db/`)
- [x] Khai báo config đường dẫn/model trong `backend/core/config.py`

### 1.3. Chuẩn output (Phase 1)
- [x] Thiết kế output tối thiểu cho 1 CV (đã tạo dataclass schema):
  - `cv_id` (filename)
  - `raw_text` (text từ PDF)
  - `extracted` (optional): email/phone/name/skills (giai đoạn đầu có thể để trống)
- [x] Thiết kế output ranking (đã tạo dataclass schema):
  - `cv_id`
  - `score` (0–100)
  - `status` (OK/ERROR)
  - `notes` (lý do lỗi, hoặc top matched snippet)

---

## 2) Backend: Parser (Day 2–4)

**File chính:** `backend/services/cv_parser.py`

### 2.1. Extract text từ PDF
- [x] Implement `extract_text_pymupdf(path) -> str`
- [x] Implement fallback `extract_text_pdfplumber(path) -> str`
- [x] Implement “normalize text”:
  - [x] chuẩn hoá unicode/whitespace
  - [x] remove line breaks thừa
  - [ ] optional: remove header/footer lặp (để Phase 1.5 nếu lâu)
  - [x] (best-effort) OCR fallback cho PDF scan (cần cài thêm Tesseract + `pytesseract`)

### 2.2. API/Interface tối thiểu
- [x] Implement `parse_cv(pdf_path) -> dict`
  - [x] trả về `cv_id`, `raw_text`, `error` nếu có
- [x] Thêm error handling:
  - [x] file không đọc được
  - [x] PDF scan (text rỗng) → trả warning “needs OCR” (Phase 1 không OCR)

### 2.4. OCR cho PDF scan (Docker-first)
Tình trạng hiện tại: đa số CV mẫu là scan → cần OCR để Phase 1 chạy end-to-end.

- [x] OCR engine được đóng gói trong Docker image (tesseract-ocr)
- [x] `pytesseract` đã được thêm vào `backend/requirements.txt`
- [ ] Re-test parser với thư mục `data/raw_cv/` (chạy trong container) và ghi lại tỉ lệ parse OK/needs OCR

### 2.3. Dữ liệu test
- [x] Thêm 5–10 CV mẫu (PDF) vào `data/raw_cv/` (đã có file PDF local; không commit nếu là dữ liệu thật)
- [x] Thêm 1–2 JD mẫu vào `data/sample_jd/` (txt)

---

## 3) Backend: Embeddings + Vector Store + Scoring (Day 5–7)

**File chính:** `backend/services/matcher.py`

### 3.1. Kết nối embeddings (Ollama)
- [x] Tạo `OllamaEmbeddings(model="nomic-embed-text")`
- [x] Thêm config model/base_url trong `backend/core/config.py` (`OLLAMA_BASE_URL`)
- [x] Docker compose đảm bảo Ollama service chạy trước app

### 3.2. Vector store (Chroma)
- [x] Khởi tạo Chroma với `persist_directory="data/chroma_db/cv_screening"`
- [x] Collection: `cvs`
- [x] Function index:
  - [x] `index_cv(cv_id, text, metadata)`
  - [x] đảm bảo id ổn định (filename)
- [x] Function reset/clear (tùy chọn):
  - [x] `reset_collection()` (dùng cho test/demo)

### 3.3. Scoring & ranking (Phase 1)
- [x] Quy ước scoring:
  - [x] query JD → `similarity_search_with_score(k=N)`
  - [x] map `distance -> similarity -> score 0–100`
  - [x] return `distance` trong `notes` để debug
- [x] Hàm `rank(jd_text) -> list[{cv_id, score, ...}]`

### 3.5. LLM review (llama3) (khuyến nghị)
- [x] Pull model chat: `docker compose exec ollama ollama pull llama3`
- [x] Tạo LLM reviewer dựa trên top chunks từ Chroma (`backend/services/llm_scorer.py`)
- [x] UI button để generate review trong Streamlit

### 3.4. Chunking (khuyến nghị, tùy thời gian)
- [x] Chunk CV text theo đoạn (mặc định 1000 chars, overlap 150)
- [x] Score theo `max` chunk similarity cho mỗi CV (gom theo `cv_id`)

---

## 4) Frontend: Streamlit MVP (Day 8–9)

**Files:** `frontend/app.py`, `frontend/pages/1_CV_Screening.py`

### 4.1. Flow UI
- [x] Nhập/paste JD (textarea)
- [x] Upload JD (PDF/TXT) và tự parse
- [x] Upload nhiều CV (file_uploader, accept pdf)
- [x] Button `Run screening`
- [x] Hiển thị bảng ranking (pandas dataframe)
- [x] Chọn 1 CV để xem:
  - [x] raw_text preview (cắt ngắn)
  - [ ] (optional) top matched snippet

### 4.2. Performance
- [x] Cache embeddings/store init bằng `st.cache_resource`
- [x] Hiển thị progress/status khi index nhiều CV

---

## 5) Tests (Day 10–11)

**Files:** `tests/test_cv_parser.py`, `tests/test_matcher.py`, `tests/test_e2e.py`

### 5.1. Unit tests — Parser
- [x] Test: parse được 1 PDF mẫu (generate PDF bằng PyMuPDF trong test)
- [x] Test: normalize không trả về None, output type đúng (covered by parser test)

### 5.2. Unit tests — Matcher
- [x] Test: index 1 đoạn text và query JD trả về score trong [0, 100] (skip nếu Ollama không chạy)
- [x] Test: reset collection (nếu có) không crash

### 5.3. E2E
- [x] Dùng 2–3 CV text (text giả) + 1 JD text → rank + review (skip nếu Ollama không chạy)

---

## 6) Documentation & Runbook (Day 12–14)

### 6.1. Run instructions
- [x] Cập nhật `README.md` hoặc thêm `PHASE_1_RUNBOOK.md`:
  - [x] pull model (embeddings + llama3)
  - [x] chạy streamlit (Docker)
  - [x] chạy tests (Docker)

### 6.2. Báo cáo kết quả
- [x] Tạo `PHASE_1_RESULTS.md` (template):
  - [ ] số CV test
  - [ ] tỉ lệ parse thành công
  - [ ] nhận xét chất lượng ranking
  - [ ] backlog cho Phase 1.5/Phase 2

---

## 7) Backlog đề xuất (không bắt buộc Phase 1)

- [ ] OCR cho CV scan (Tesseract hoặc dịch vụ local)
- [ ] Chunking + section-aware scoring (Skills/Experience/Education)
- [ ] Giải thích score: trích top chunks match (evidence)
- [ ] Dedup CV, xử lý multi-language (VI/EN)
- [ ] FastAPI endpoints cho CV screening (Phase 2)

---

## 8) Lệnh chạy nhanh (tham khảo)

```bash
# 1) tạo venv
python -m venv .venv
.venv\Scripts\activate

# 2) cài deps (sẽ điền trong backend/requirements.txt)
pip install -r backend/requirements.txt

# 3) pull embeddings model
ollama pull nomic-embed-text

# 4) chạy UI
cd frontend
streamlit run app.py

# 5) chạy test
cd ..
pytest -q
```
