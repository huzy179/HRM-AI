# 🚀 HRM AI: Tối ưu hóa Tuyển dụng & Hội nhập với LLM và RAG
*(Intelligent Recruitment & Onboarding Platform)*

## 📖 Giới thiệu Dự án (Overview)
**HRM AI** là một hệ sinh thái quản trị nhân sự toàn diện được hỗ trợ bởi Trí tuệ Nhân tạo (GenAI). Dự án nhằm giải quyết hai vấn đề lớn nhất của bộ phận Nhân sự hiện nay: Quá tải trong việc sàng lọc hồ sơ ứng viên và Tốn thời gian giải đáp các thắc mắc lặp đi lặp lại của nhân viên mới.

Dự án áp dụng kiến trúc **RAG (Retrieval-Augmented Generation)** và **Local LLM** (chạy hoàn toàn offline trên máy tính), đảm bảo tuyệt đối tính bảo mật dữ liệu nội bộ của doanh nghiệp.

### 🌟 Các Module Chính (Key Modules)
Hệ thống được chia thành 3 phân hệ chính, tương ứng với nhiệm vụ của 3 thành viên:
1. **AI-based CV Screening (Tuyển dụng thông minh):** 
   - Tự động đọc và trích xuất dữ liệu (Parse) từ hàng loạt CV (PDF/Word).
   - So khớp ngữ nghĩa giữa CV và Mô tả công việc (Job Description) để chấm điểm và xếp hạng ứng viên.
2. **Company Policy Chatbot (Trợ lý Hội nhập):**
   - Ứng dụng RAG để cho phép HR tải lên Sổ tay nhân viên, Quy chế công ty.
   - Chatbot giải đáp chính xác, tự nhiên mọi câu hỏi của nhân viên mới trích xuất từ dữ liệu nội bộ mà không bịaa đặt thông tin (Zero Hallucination).
3. **Centralized HR Dashboard (Cổng quản trị):**
   - Giao diện người dùng thân thiện dành cho HR để quản lý chiến dịch tuyển dụng và tương tác với AI.

---

## 🛠 Công nghệ sử dụng (Tech Stack)

Dự án sử dụng các công nghệ hiện đại và chuẩn công nghiệp nhất hiện nay:

*   **Ngôn ngữ lập trình:** Python 3.10+
*   **Mô hình Ngôn ngữ Lớn (LLMs & AI):**
    *   **Ollama:** Chạy Local LLM, tối ưu hóa cho kiến trúc Apple Silicon (Mac M-Series).
    *   **LLM Core:** Llama-3 (8B) cho Chatbot sinh văn bản.
    *   **Embeddings:** `nomic-embed-text` cho việc tạo vector ngữ nghĩa.
*   **Khung RAG (RAG Framework):** LangChain.
*   **Cơ sở dữ liệu Vector (Vector DB):** ChromaDB (Local).
*   **Xử lý Tài liệu & NLP:** `PyMuPDF` (đọc PDF), `spaCy`, `scikit-learn` (tính toán Cosine Similarity).
*   **Hệ thống (System Architecture):**
    *   **Backend / API:** FastAPI + Uvicorn.
    *   **Frontend / UI:** Streamlit (Tạo giao diện Web nhanh chóng).

---

## 📁 Cấu trúc thư mục (Project Structure)

Dự án được tổ chức theo mô hình Client-Server nhẹ, phân tách rõ RAG logic và UI:

```text
hrm-ai-project/
│
├── backend/                    # TOÀN BỘ LOGIC AI VÀ API NẰM Ở ĐÂY
│   ├── api/                    
│   │   ├── cv_routes.py        # Các API (Endpoint) xử lý CV Screening
│   │   └── chat_routes.py      # Các API xử lý Chatbot RAG
│   │
│   ├── core/
│   │   ├── config.py           # Cấu hình hệ thống (đường dẫn DB, tên model)
│   │   └── prompts.py          # Lưu các template prompt cho LangChain
│   │
│   ├── services/               # CHỨA LOGIC CHÍNH CỦA DỰ ÁN
│   │   ├── cv_parser.py        # Logic đọc PDF và OCR CV
│   │   ├── matcher.py          # Thuật toán chấm điểm CV vs JD
│   │   └── rag_engine.py       # Logic LangChain cắt file, đưa vào ChromaDB
│   │
│   ├── main.py                 # File khởi chạy FastAPI server
│   └── requirements.txt        # Các thư viện Python cần thiết
│
├── frontend/                   # GIAO DIỆN NGƯỜI DÙNG (UI) NẰM Ở ĐÂY
│   ├── app.py                  # File chính của Streamlit (Menu điều hướng)
│   ├── pages/
│   │   ├── 1_Dashboard.py      # Trang tổng quan
│   │   ├── 2_CV_Screening.py   # Trang Upload CV và xem kết quả xếp hạng
│   │   └── 3_Policy_Chat.py    # Giao diện Chatbot cho nhân viên
│   └── assets/                 # Logo, hình ảnh, CSS tùy chỉnh
│
├── data/                       # DỮ LIỆU ĐẦU VÀO & LƯU TRỮ TRONG QUÁ TRÌNH CHẠY
│   ├── raw_cv/                 # Thư mục chứa CV mẫu để test
│   ├── policy_docs/            # Thư mục chứa Sổ tay nhân viên, Luật LĐ (PDF)
│   └── chroma_db/              # Nơi ChromaDB lưu trữ vector dữ liệu (tự động tạo)
│
├── .gitignore                  # File ẩn những file không cần đưa lên Github
└── README.md                   # File tài liệu bạn đang đọc