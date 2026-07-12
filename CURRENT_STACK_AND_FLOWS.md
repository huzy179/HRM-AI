# HRM AI - Current Stack And Flows

Tài liệu này mô tả dự án đang dùng những công nghệ gì, dùng để làm gì, và luồng nghiệp vụ hiện tại vận hành như thế nào. Không đi vào chi tiết code.

## 1. Mục Tiêu Sản Phẩm

HRM AI là hệ thống hỗ trợ tuyển dụng và tra cứu tài liệu nội bộ bằng AI.

Hệ thống hiện có 2 nhóm chức năng chính:

- **CV Screening**: tạo campaign tuyển dụng, upload JD và CV ứng viên, sau đó hệ thống parse tài liệu, chấm điểm phù hợp, xếp hạng ứng viên và tạo review bằng LLM.
- **Policy Chatbot**: upload tài liệu/chính sách nội bộ, index vào vector database, sau đó chat với tài liệu và nhận câu trả lời có citation.

## 2. Stack Đang Dùng

### Frontend

- **Next.js + React + TypeScript**: xây giao diện web.
- **Tailwind CSS**: styling UI.
- **Lucide React**: icon trong giao diện.

Mục đích: cung cấp màn hình thao tác cho người dùng, gồm CV screening, policy chat, upload tài liệu và xem kết quả.

### Backend API

- **FastAPI**: cung cấp REST API cho frontend.
- **Uvicorn**: chạy server FastAPI.
- **Pydantic**: validate dữ liệu request/response.

Mục đích: nhận upload, tạo campaign, điều phối job, trả trạng thái xử lý, expose kết quả ranking/review/chat.

### Database

- **PostgreSQL**: database chính khi chạy Docker.
- **SQLAlchemy**: ORM để backend làm việc với database.
- **Alembic**: migration schema.
- **SQLite**: dùng chủ yếu cho test/local lightweight.

Mục đích: lưu campaign, JD, CV, ứng viên, kết quả screening, review, job status, audit log và policy document metadata.

### Queue Và Worker

- **Redis**: message broker cho hàng đợi.
- **RQ**: queue/job runner.
- **worker_parse**: xử lý parse/OCR JD và CV.
- **worker_index**: xử lý indexing, ranking, policy ingest, rebuild index, cleanup.
- **worker_llm**: xử lý các tác vụ gọi LLM như review ứng viên.

Mục đích: tách các tác vụ nặng hoặc chậm ra khỏi API để UI không bị treo khi upload nhiều CV, OCR, embedding hoặc gọi LLM.

### Local LLM

- **Ollama**: chạy model local/offline.
- **nomic-embed-text**: embedding model cho RAG/ranking.
- **llama3**: chat/review model mặc định.

Mục đích: giảm phụ thuộc cloud API, hỗ trợ chạy local, dùng cho embedding, RAG, review ứng viên và sinh nội dung tự động.

### Vector Database Và RAG

- **ChromaDB**: lưu vector embeddings.
- **LangChain Ollama integration**: kết nối Ollama với embedding/chat model.
- **LangChain Chroma integration**: kết nối backend với Chroma.

Mục đích: tìm kiếm ngữ nghĩa trên CV/JD/policy document, phục vụ ranking ứng viên và policy chatbot có citation.

### Document Processing

- **PyMuPDF**: đọc text từ PDF.
- **pdfplumber**: fallback khi PDF text extraction chưa tốt.
- **Tesseract + pytesseract**: OCR cho PDF scan hoặc file không có text layer.
- **python-docx**: đọc DOCX.

Mục đích: chuyển JD, CV và policy document thành text sạch để dùng cho ranking, RAG và review.

### Observability

- **Prometheus**: scrape metrics từ backend.
- **Grafana**: dashboard quan sát hệ thống.
- **Loki + Promtail**: thu thập và xem log container.
- **Jaeger + OpenTelemetry**: trace request và luồng xử lý.

Mục đích: theo dõi health, request latency, metrics của job/RAG, log hệ thống và trace khi debug.

### Evaluation

- **Ragas**: đánh giá chất lượng Policy RAG.

Mục đích: đo faithfulness, context precision/recall và answer relevancy cho chatbot tài liệu.

### Runtime Và Dev Tooling

- **Docker Compose**: chạy full stack local.
- **Makefile**: gom lệnh vận hành thường dùng.
- **pytest**: test backend/API/worker logic.

Mục đích: giúp setup, chạy, test và debug dự án nhất quán hơn.

## 3. Docker Services Hiện Tại

- **frontend**: web UI tại `http://localhost:3000`.
- **api**: FastAPI tại `http://localhost:8000`.
- **postgres**: database tại port `5432`.
- **redis**: queue backend tại port `6379`.
- **ollama**: local model server tại port `11434`.
- **worker_parse**: worker cho parse/OCR.
- **worker_index**: worker cho index/ranking/RAG ingest.
- **worker_llm**: worker cho LLM review.
- **prometheus**: metrics tại `http://localhost:9090`.
- **grafana**: dashboard tại `http://localhost:3001`.
- **loki**: log store tại `http://localhost:3100`.
- **promtail**: đẩy container logs sang Loki.
- **jaeger**: trace UI tại `http://localhost:16686`.

Service **worker** legacy vẫn còn trong compose profile `legacy`, dùng khi muốn chạy một worker all-in-one thay vì 3 worker tách riêng.

## 4. Cách Chạy Khuyến Nghị

Chạy lần đầu:

```bash
make setup
```

Chạy lại stack:

```bash
make up
```

Xem log app chính:

```bash
make logs
```

Kiểm tra health:

```bash
make health
```

Pull lại model Ollama:

```bash
make models
```

Xem danh sách URL:

```bash
make urls
```

## 5. Flow CV Screening

Mục tiêu: tuyển dụng theo từng campaign/vị trí.

Ví dụ:

- Campaign: `Backend Developer - Tháng 7/2026`
- JD: `backend_developer_jd.pdf`
- CVs: toàn bộ CV ứng tuyển vị trí Backend Developer

Luồng sử dụng:

1. Người dùng tạo campaign tuyển dụng.
2. Upload JD cho campaign đó.
3. Upload nhiều CV ứng viên vào cùng campaign.
4. Worker parse/OCR chuyển JD và CV thành text.
5. Worker index/ranking tạo embeddings và so sánh JD với CV.
6. Hệ thống trả bảng ranking ứng viên.
7. Người dùng có thể yêu cầu LLM review từng ứng viên.
8. Kết quả cuối gồm điểm match, evidence/citation, nhận xét, strengths/gaps và trạng thái pipeline.

Ý nghĩa:

- Campaign là “ngữ cảnh tuyển dụng”.
- JD là yêu cầu của vị trí.
- CVs là tập ứng viên cho vị trí đó.
- Ranking giúp lọc nhanh.
- LLM review giúp có nhận xét đọc được bởi recruiter/hiring manager.

## 6. Flow Policy Chatbot

Mục tiêu: chat với tài liệu/chính sách nội bộ.

Luồng sử dụng:

1. Người dùng upload tài liệu policy, ví dụ quy chế nghỉ phép, bảo hiểm, onboarding, handbook.
2. Worker parse tài liệu thành text.
3. Worker index text vào ChromaDB.
4. Người dùng đặt câu hỏi trong màn Policy Chat.
5. Backend retrieve các đoạn liên quan từ vector database.
6. LLM trả lời dựa trên context tìm được.
7. UI hiển thị câu trả lời kèm citations.

Lưu ý vận hành:

- Nếu chưa upload tài liệu hoặc tài liệu chưa ingest xong, chatbot không có ngữ cảnh để trả lời.
- Cần có model `nomic-embed-text` cho retrieval.
- Cần có model `llama3` hoặc model chat tương đương cho phần trả lời.

## 7. Flow Observability

Mục tiêu: biết hệ thống có đang chạy ổn không và lỗi nằm ở đâu.

Luồng sử dụng:

1. API expose metrics tại `/metrics/prometheus`.
2. Prometheus scrape metrics định kỳ.
3. Grafana đọc Prometheus/Loki/Jaeger để hiển thị dashboard.
4. Promtail gom log container và gửi sang Loki.
5. OpenTelemetry gửi traces sang Jaeger.

Nên dùng khi:

- API chậm hoặc lỗi.
- Worker không xử lý job.
- RAG trả lời chậm hoặc không có citation.
- Cần xem log theo service.
- Cần trace request qua API/DB/LLM.

## 8. Flow Evaluation

Mục tiêu: đánh giá chất lượng RAG thay vì chỉ nhìn cảm tính.

Luồng sử dụng:

1. Chuẩn bị bộ câu hỏi đánh giá trong `evals/policy_eval_questions.jsonl`.
2. Chạy Ragas eval.
3. Xem kết quả về answer relevancy, context precision, context recall và faithfulness.

Chạy:

```bash
make ragas-venv
make ragas
```

## 9. Các URL Chính

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (`admin` / `admin`)
- Loki: `http://localhost:3100`
- Jaeger: `http://localhost:16686`

## 10. Ghi Chú Hiện Trạng

- Kiến trúc hiện tại phù hợp cho local development, demo và prototype AI workflow.
- Docker Compose đang là đường chạy chính.
- Worker đã được tách theo nhóm trách nhiệm để dễ debug và scale từng phần.
- Policy chatbot là RAG theo tài liệu, không phải general chatbot.
- CV screening đang đi theo mô hình campaign-based: một campaign tương ứng một vị trí tuyển dụng hoặc một đợt tuyển.
- Observability đã có nền tảng cơ bản, nhưng dashboard/alert/SLO có thể tiếp tục hoàn thiện sau.
