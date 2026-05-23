from __future__ import annotations

from pathlib import Path

import pytest
import requests

from backend.core.config import Settings
from backend.services.matcher import CVMatcher


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(base_url, timeout=2)
        return r.status_code < 500
    except Exception:
        return False


@pytest.mark.parametrize("base_url", ["http://localhost:11434", "http://ollama:11434"])
def test_rank_returns_scores(tmp_path: Path, base_url: str) -> None:
    if not _ollama_available(base_url):
        pytest.skip(f"Ollama not available at {base_url}")

    data_dir = tmp_path / "data"
    chroma_dir = data_dir / "chroma_db" / "cv_screening"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        project_root=tmp_path,
        raw_cv_dir=data_dir / "raw_cv",
        sample_jd_dir=data_dir / "sample_jd",
        policy_docs_dir=data_dir / "policy_docs",
        chroma_dir=data_dir / "chroma_db",
        chroma_cv_screening_dir=chroma_dir,
        chroma_collection_cvs="cvs_test",
        tenant_id="default",
        ollama_embed_model="nomic-embed-text",
        ollama_base_url=base_url,
        ollama_chat_model="llama3",
        ollama_timeout_s=60,
        ollama_retries=2,
        ollama_retry_backoff_s=1.0,
        cv_chunk_size=400,
        cv_chunk_overlap=50,
    )

    matcher = CVMatcher(settings)
    matcher.reset_collection()

    matcher.index_cv(cv_id="cv_a", cv_text="Python FastAPI Docker", metadata={"filename": "cv_a"})
    matcher.index_cv(cv_id="cv_b", cv_text="Sales marketing CRM", metadata={"filename": "cv_b"})

    ranked = matcher.rank(jd_text="Need a Python engineer with FastAPI and Docker", k=10)
    assert ranked
    assert all(0.0 <= r.score <= 100.0 for r in ranked)
    assert ranked[0].cv_id == "cv_a"
