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
- [ ] Cài Python 3.10+
- [ ] Tạo virtualenv (khuyến nghị `.venv/`)
- [ ] Cài Ollama
- [ ] Pull embeddings model: `ollama pull nomic-embed-text`
- [x] Chuẩn bị dependencies Python (`backend/requirements.txt`)

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

### 2.2. API/Interface tối thiểu
- [x] Implement `parse_cv(pdf_path) -> dict`
  - [x] trả về `cv_id`, `raw_text`, `error` nếu có
- [x] Thêm error handling:
  - [x] file không đọc được
  - [x] PDF scan (text rỗng) → trả warning “needs OCR” (Phase 1 không OCR)

### 2.3. Dữ liệu test
- [ ] Thêm 5–10 CV mẫu (PDF) vào `data/raw_cv/` (không commit nếu là dữ liệu thật)
- [x] Thêm 1–2 JD mẫu vào `data/sample_jd/` (txt)

---

## 3) Backend: Embeddings + Vector Store + Scoring (Day 5–7)

**File chính:** `backend/services/matcher.py`

### 3.1. Kết nối embeddings (Ollama)
- [ ] Tạo `OllamaEmbeddings(model="nomic-embed-text")`
- [ ] Thêm config model name trong `backend/core/config.py`
- [ ] Ghi chú rõ: Ollama phải chạy (daemon) trước khi chạy app

### 3.2. Vector store (Chroma)
- [ ] Khởi tạo Chroma với `persist_directory="data/chroma_db/cv_screening"`
- [ ] Collection: `cvs`
- [ ] Function index:
  - [ ] `index_cv(cv_id, text, metadata)`
  - [ ] đảm bảo id ổn định (filename)
- [ ] Function reset/clear (tùy chọn):
  - [ ] `reset_collection()` (dùng cho test/demo)

### 3.3. Scoring & ranking (Phase 1)
- [ ] Quy ước scoring:
  - [ ] query JD → `similarity_search_with_score(k=N)`
  - [ ] map `distance -> similarity -> score 0–100`
  - [ ] Nên log/return `top_hit_distance` để debug
- [ ] Hàm `rank_cvs(jd_text) -> list[{cv_id, score, ...}]`

### 3.4. Chunking (khuyến nghị, tùy thời gian)
- [ ] (Optional) Chunk CV text theo đoạn (ví dụ 800–1200 chars) trước khi index
- [ ] (Optional) Score theo `max` chunk similarity cho mỗi CV

---

## 4) Frontend: Streamlit MVP (Day 8–9)

**Files:** `frontend/app.py`, `frontend/pages/1_CV_Screening.py`

### 4.1. Flow UI
- [ ] Nhập/paste JD (textarea)
- [ ] Upload nhiều CV (file_uploader, accept pdf)
- [ ] Button `Run screening`
- [ ] Hiển thị bảng ranking (pandas dataframe)
- [ ] Chọn 1 CV để xem:
  - [ ] raw_text preview (cắt ngắn)
  - [ ] (optional) top matched snippet

### 4.2. Performance
- [ ] Cache embeddings/store init bằng `st.cache_resource`
- [ ] Hiển thị progress/status khi index nhiều CV

---

## 5) Tests (Day 10–11)

**Files:** `tests/test_cv_parser.py`, `tests/test_matcher.py`, `tests/test_e2e.py`

### 5.1. Unit tests — Parser
- [ ] Test: parse được 1 PDF mẫu (nếu repo không có PDF mẫu thì mock/skip)
- [ ] Test: normalize không trả về None, output type đúng

### 5.2. Unit tests — Matcher
- [ ] Test: index 1 đoạn text và query JD trả về score trong [0, 100]
- [ ] Test: reset collection (nếu có) không crash

### 5.3. E2E
- [ ] Dùng 2–3 CV text (có thể text giả) + 1 JD text → rank list có thứ tự hợp lý

---

## 6) Documentation & Runbook (Day 12–14)

### 6.1. Run instructions
- [ ] Cập nhật `README.md` hoặc thêm `PHASE_1_RUNBOOK.md`:
  - [ ] cài Ollama + pull model
  - [ ] cài deps python
  - [ ] chạy streamlit
  - [ ] chạy tests

### 6.2. Báo cáo kết quả
- [ ] Tạo `PHASE_1_RESULTS.md`:
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
