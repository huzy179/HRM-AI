from __future__ import annotations

from pathlib import Path

import pytest
import requests

from backend.core.config import Settings
from backend.services.policy_rag import PolicyRAG


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(base_url, timeout=2)
        return r.status_code < 500
    except Exception:
        return False


@pytest.mark.parametrize("base_url", ["http://localhost:11434", "http://ollama:11434"])
def test_policy_rag_ingest_and_answer(tmp_path: Path, base_url: str) -> None:
    if not _ollama_available(base_url):
        pytest.skip(f"Ollama not available at {base_url}")

    data_dir = tmp_path / "data"
    chroma_dir = data_dir / "chroma_db"
    (chroma_dir / "cv_screening").mkdir(parents=True, exist_ok=True)

    settings = Settings(
        project_root=tmp_path,
        raw_cv_dir=data_dir / "raw_cv",
        sample_jd_dir=data_dir / "sample_jd",
        policy_docs_dir=data_dir / "policy_docs",
        chroma_dir=chroma_dir,
        chroma_cv_screening_dir=chroma_dir / "cv_screening",
        chroma_collection_cvs="cvs_policy_e2e",
        ollama_embed_model="nomic-embed-text",
        ollama_base_url=base_url,
        ollama_chat_model="llama3",
        ollama_timeout_s=60,
        ollama_retries=1,
        ollama_retry_backoff_s=0.5,
        cv_chunk_size=400,
        cv_chunk_overlap=50,
    )

    rag = PolicyRAG(settings=settings)
    rag.ingest_text(
        doc_id="doc1",
        source="policy.txt",
        text="Quy định nghỉ phép: Nhân viên được 12 ngày phép/năm. Quy trình: gửi đơn trước 3 ngày làm việc.",
    )

    ans = rag.answer(query="Nhân viên có bao nhiêu ngày phép một năm?", k=3)
    assert isinstance(ans.answer, str) and ans.answer.strip()
    assert isinstance(ans.citations, list)
    assert ans.citations  # should retrieve from ingested chunks

