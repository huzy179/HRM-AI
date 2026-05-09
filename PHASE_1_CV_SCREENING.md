# 📋 PHASE 1: CV Screening (Tuyển dụng Thông minh)

**Thời gian dự kiến:** 2 tuần (10-14 ngày)  
**Mục tiêu:** Xây dựng một hệ thống có thể đọc CV, trích xuất thông tin, so khớp với Job Description, và xếp hạng ứng viên.

---

## 🎯 Mục Tiêu Giai Đoạn 1

### Kết Quả Mong Muốn
- ✅ Có thể tự động parse PDF CV → Trích xuất dữ liệu cấu trúc
- ✅ So khớp ngữ nghĩa (semantic matching) giữa CV vs Job Description
- ✅ Chấm điểm & xếp hạng ứng viên tự động
- ✅ Có 1 CLI script hoặc Streamlit dashboard đơn giản để test

### Deliverables
- `cv_parser.py` - Module đọc & parse CV
- `matcher.py` - Module chấm điểm CV
- `test_cv_screening.py` - Test script đơn giản
- `requirements.txt` - Dependencies
- 5-10 CV mẫu để test

---

## 🛠 Tech Stack Giai Đoạn 1

| Công nghệ | Mục đích | Tại sao chọn |
|-----------|---------|-------------|
| **PyMuPDF** | Parse PDF | Nhẹ, nhanh, không cần Poppler |
| **pdfplumber** | Đọc text từ PDF | Dự phòng nếu PyMuPDF không ok |
| **LangChain** | Orchestration | Chuẩn hoá pipeline embedding/retrieval |
| **Ollama + `nomic-embed-text`** | Embeddings | Local/offline, dễ vận hành |
| **ChromaDB** | Vector DB | Local, nhẹ, phù hợp Phase 1 |
| **spaCy** *(optional)* | NLP - Trích xuất entities | Khi cần extract email/phone tốt hơn regex |
| **pandas** | Xử lý dữ liệu | Chuẩn bị dữ liệu output |
| **Streamlit** | UI dashboard | Nhanh, không cần frontend riêng |

---

## 📁 Cấu Trúc File Giai Đoạn 1

```
hrm-ai-project/
│
├── backend/
│   ├── services/
│   │   ├── cv_parser.py           # ⭐ Parser CV → Extract info
│   │   ├── matcher.py              # ⭐ So khớp CV vs JD, chấm điểm
│   │   └── utils.py                # Helper functions
│   │
│   ├── core/
│   │   ├── config.py               # Config đường dẫn, model names
│   │   └── schemas.py              # Data classes (CV, JD, Result)
│   │
│   ├── requirements.txt             # Python dependencies
│   └── main.py                     # FastAPI server (chưa cần ở giai đoạn này)
│
├── frontend/
│   ├── app.py                      # Streamlit - Trang chính
│   └── pages/
│       └── 1_CV_Screening.py       # Trang upload & xem kết quả
│
├── data/
│   ├── raw_cv/                     # Thư mục chứa CV mẫu
│   │   ├── cv_sample_1.pdf
│   │   ├── cv_sample_2.pdf
│   │   └── ...
│   │
│   └── sample_jd/                  # Thư mục chứa Job Description mẫu
│       ├── jd_software_engineer.txt
│       └── jd_product_manager.txt
│
├── tests/
│   ├── test_cv_parser.py           # Unit test CV Parser
│   ├── test_matcher.py             # Unit test Matcher
│   └── test_e2e.py                 # End-to-end test
│
├── PHASE_1_CV_SCREENING.md         # File này
└── README.md                       # README chính
```

---

## 📅 Timeline Chi Tiết

### **Tuần 1: CV Parser & Setup**

#### **Ngày 1-2: Setup Project Structure**
```bash
# 1. Tạo folder structure
mkdir -p hrm-ai-project/{backend/{services,core,api},frontend/pages,data/{raw_cv,sample_jd},tests}

# 2. Tạo requirements.txt
# 3. Tạo .gitignore
# 4. git init & first commit
```

**Files cần tạo:**
- [ ] `backend/requirements.txt`
- [ ] `backend/core/config.py`
- [ ] `backend/core/schemas.py` (Data classes)
- [ ] `.gitignore`

**Commit:** `feat: Initial project structure`

---

#### **Ngày 3-4: CV Parser Implementation**
**Mục tiêu:** Parse 1 PDF → Output structured data

**Code CV Parser cơ bản:**

```python
# backend/services/cv_parser.py

import fitz  # PyMuPDF
import re
from pathlib import Path

class CVParser:
    def __init__(self):
        self.pdf_path = None
        self.raw_text = ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from PDF file
        """
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def parse(self, pdf_path: str) -> dict:
        """
        Parse CV and return structured data
        """
        self.raw_text = self.extract_text_from_pdf(pdf_path)
        
        # Extract basic info (tạm thời dùng regex)
        extracted = {
            "full_text": self.raw_text,
            "skills": self._extract_skills(),
            "experience": self._extract_experience(),
            "education": self._extract_education(),
        }
        
        return extracted
    
    def _extract_skills(self) -> list:
        # Tìm từ khóa kỹ năng trong text
        # Ví dụ: Python, JavaScript, SQL, etc.
        pass
    
    def _extract_experience(self) -> list:
        # Tìm công việc trước đó, duration
        pass
    
    def _extract_education(self) -> list:
        # Tìm trình độ học vấn
        pass
```

**Deliverables Ngày 3-4:**
- [ ] `backend/services/cv_parser.py` - Parse text từ PDF
- [ ] Test parse 1 CV thành công
- [ ] Commit: `feat: Implement basic CV parser`

---

#### **Ngày 5-7: Ollama Embeddings + LangChain + Chroma (Matching & Scoring)**
**Mục tiêu:** So khớp CV vs Job Description bằng Ollama embeddings và Chroma similarity search

**Code Matcher cơ bản:**

```python
# backend/services/matcher.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

class CVMatcher:
    def __init__(
        self,
        *,
        chroma_dir: str = "data/chroma_db/cv_screening",
        collection_name: str = "cvs",
        embed_model: str = "nomic-embed-text",
    ) -> None:
        self.embeddings = OllamaEmbeddings(model=embed_model)
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=chroma_dir,
        )
    
    def index_cv(self, *, cv_id: str, cv_text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Index 1 CV vào Chroma (Phase 1: 1 CV = 1 document).
        """
        self.store.add_texts(
            texts=[cv_text],
            metadatas=[{**(metadata or {}), "cv_id": cv_id}],
            ids=[cv_id],
        )

    def score_cv_against_jd(self, *, cv_id: str, jd_text: str, k: int = 20) -> float:
        """
        Score 0-100 dựa trên retrieval score của Chroma cho JD (query).
        Gợi ý Phase 1: lấy similarity tốt nhất của đúng cv_id trong top-k.
        """
        hits = self.store.similarity_search_with_score(jd_text, k=k)
        best_similarity = 0.0
        for doc, distance in hits:
            hit_id = (doc.metadata or {}).get("cv_id")
            if hit_id != cv_id:
                continue
            # Chroma thường trả về distance (càng nhỏ càng giống). Quy đổi thô về similarity.
            similarity = 1.0 / (1.0 + float(distance))
            best_similarity = max(best_similarity, similarity)
        return round(best_similarity * 100.0, 2)
    
    def score_multiple_cvs(self, cv_texts: list, jd_text: str) -> list:
        """
        Score multiple CVs against single JD
        Returns: list of (cv_name, score) sorted by score DESC
        """
        results = []
        for cv_name, cv_text in cv_texts:
            self.index_cv(cv_id=cv_name, cv_text=cv_text, metadata={"filename": cv_name})
            score = self.score_cv_against_jd(cv_id=cv_name, jd_text=jd_text)
            results.append({
                "cv_name": cv_name,
                "score": score
            })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
```

**Deliverables Ngày 5-7:**
- [ ] `backend/services/matcher.py` - Similarity matching
- [ ] Test với 3 CV + 1 JD mẫu
- [ ] Verify kết quả hợp lý
- [ ] Commit: `feat: CV-JD matching with Ollama embeddings`

---

### **Tuần 2: UI Dashboard & Testing**

#### **Ngày 8-9: Streamlit Dashboard**
**Mục tiêu:** Tạo giao diện upload CV & xem kết quả

```python
# frontend/pages/1_CV_Screening.py

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add backend to path
sys.path.append("../../backend")

from services.cv_parser import CVParser
from services.matcher import CVMatcher

def main():
    st.title("📋 CV Screening System")
    
    # Upload Job Description
    st.header("Step 1: Upload Job Description")
    jd_file = st.file_uploader("Upload JD (TXT)", type="txt")
    jd_text = ""
    if jd_file:
        jd_text = jd_file.read().decode("utf-8")
        st.success("JD loaded successfully")
    
    # Upload CVs
    st.header("Step 2: Upload CVs")
    cv_files = st.file_uploader(
        "Upload CV files (PDF)",
        type="pdf",
        accept_multiple_files=True
    )
    
    # Process & Score
    if st.button("🚀 Score CVs", key="score_btn"):
        if not jd_text:
            st.error("Please upload Job Description first!")
            return
        
        if not cv_files:
            st.error("Please upload at least 1 CV!")
            return
        
        parser = CVParser()
        matcher = CVMatcher()
        
        results = []
        
        with st.spinner("Processing CVs..."):
            for cv_file in cv_files:
                # Save temp file
                temp_path = f"/tmp/{cv_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(cv_file.getbuffer())
                
                # Parse CV
                cv_data = parser.parse(temp_path)
                
                # Score
                score = matcher.calculate_similarity(
                    cv_data["full_text"],
                    jd_text
                )
                
                results.append({
                    "CV Name": cv_file.name,
                    "Score": score,
                    "Status": "✅" if score > 70 else "⏳"
                })
        
        # Display results
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values("Score", ascending=False)
        
        st.header("📊 Results")
        st.dataframe(
            df_results.style.highlight_max(subset=["Score"], color='lightgreen'),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
```

**Deliverables Ngày 8-9:**
- [ ] `frontend/pages/1_CV_Screening.py` - Streamlit dashboard
- [ ] `frontend/app.py` - Main entry point
- [ ] Test UI hoạt động
- [ ] Commit: `feat: Add Streamlit dashboard for CV screening`

---

#### **Ngày 10-14: Testing & Optimization**

**Ngày 10-11: Unit Tests**
```python
# tests/test_cv_parser.py
import pytest
from backend.services.cv_parser import CVParser

def test_extract_text_from_pdf():
    parser = CVParser()
    text = parser.extract_text_from_pdf("data/raw_cv/sample_1.pdf")
    assert len(text) > 0
    assert isinstance(text, str)

# tests/test_matcher.py
def test_similarity_score():
    matcher = CVMatcher()
    cv = "Python Django Flask AWS"
    jd = "Looking for Python developer with Django experience"
    score = matcher.calculate_similarity(cv, jd)
    assert 0 <= score <= 100
    assert score > 50  # Should be reasonably high
```

**Deliverables Ngày 10-11:**
- [ ] `tests/test_cv_parser.py`
- [ ] `tests/test_matcher.py`
- [ ] Run tests: `pytest tests/`
- [ ] Commit: `test: Add unit tests for CV screening`

**Ngày 12-14: End-to-End Testing & Documentation**
- [ ] Chuẩn bị 5-10 CV mẫu thực tế
- [ ] Test với 2-3 Job Description thực tế
- [ ] Verify kết quả có hợp lý
- [ ] Viết `PHASE_1_RESULTS.md` - Báo cáo kết quả
- [ ] Cleanup code & add comments
- [ ] Final commit: `docs: Phase 1 complete with E2E testing`

---

## 📊 Acceptance Criteria

Phase 1 hoàn thành khi:

- [x] Có thể parse 100% PDF CV thành công
- [x] Trích xuất được ít nhất 3 loại thông tin (skills, experience, education)
- [x] Chấm điểm CV vs JD có kết quả hợp lý (0-100)
- [x] Có Streamlit dashboard để upload & xem kết quả
- [x] Có unit tests cover chính các functions
- [x] Code có documentation (docstrings, comments)
- [x] Tất cả push lên GitHub, không có merge conflicts

---

## 🚀 Cách Chạy Phase 1

### Setup Environment
```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Download spaCy model
python -m spacy download en_core_web_sm
```

### Cài & chạy Ollama (bắt buộc cho embeddings)
```bash
# 1) Cài Ollama (Windows/Mac/Linux): https://ollama.com

# 2) Kéo model embeddings về máy
ollama pull nomic-embed-text
```

### Run Streamlit Dashboard
```bash
cd frontend
streamlit run app.py
```

### Run Tests
```bash
cd ..
pytest tests/ -v
```

---

## 📝 requirements.txt (Phase 1)

```
# PDF Processing
PyMuPDF==1.23.8
pdfplumber==0.10.3

# LangChain + Ollama + Vector DB
langchain==0.3.0
langchain-ollama==0.2.0
langchain-chroma==0.1.4
chromadb==0.5.5

# Data Processing
pandas==2.1.3
numpy==1.26.2

# Web UI
streamlit==1.29.0

# Testing
pytest==7.4.3

# Utilities
python-dotenv==1.0.0

# NLP (optional)
spacy==3.7.2
```

---

## 🎓 Học Tập & Resources

Trong giai đoạn này, bạn sẽ học:
- ✅ Làm việc với PDF trong Python
- ✅ Embeddings local với Ollama
- ✅ LangChain pipeline (embed → vector store → retrieval)
- ✅ Vector DB (Chroma) & similarity search
- ✅ Xây dựng Streamlit app
- ✅ Unit testing Python

**Recommended Resources:**
- [Ollama Docs](https://ollama.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Streamlit Tutorial](https://docs.streamlit.io/)
- [spaCy 101](https://spacy.io/usage/101)
- [PyMuPDF Docs](https://pymupdf.readthedocs.io/)

---

## ❓ Q&A / Troubleshooting

**Q: CV Parser không đọc được một số PDF?**  
A: Một số PDF có encoding đặc biệt. Thử dùng `pdfplumber` thay thế, hoặc chuyển PDF → PNG → OCR (tạm chưa cần).

**Q: Similarity score quá thấp/cao?**  
A: Thử chunking CV rồi lấy max/avg similarity theo chunk, hoặc tune lại cách normalize text (bỏ header/footer lặp).

**Q: Streamlit app chậm?**  
A: Cache model embedding: `@st.cache_resource def load_model():`

**Q: Làm sao deploy lên production sau?**  
A: Phase 2 sẽ dùng FastAPI backend, connect từ frontend.

---

**Last Updated:** May 9, 2026  
**Status:** 🟢 Ready to Start
