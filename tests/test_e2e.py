from __future__ import annotations

from pathlib import Path

import pytest
import requests

from backend.core.config import Settings
from backend.core.schemas import CVParseResult
from backend.services.llm_scorer import review_with_llama3
from backend.services.matcher import CVMatcher


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(base_url, timeout=2)
        return r.status_code < 500
    except Exception:
        return False


@pytest.mark.parametrize("base_url", ["http://localhost:11434", "http://ollama:11434"])
def test_e2e_rank_and_review(tmp_path: Path, base_url: str) -> None:
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
        chroma_collection_cvs="cvs_e2e",
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

    cvs = [
        CVParseResult(cv_id="cv_best", raw_text="3 years Python. FastAPI APIs. Docker in production.", error=None),
        CVParseResult(cv_id="cv_other", raw_text="HR admin, payroll, Excel.", error=None),
    ]
    matcher.index_cvs(cvs)

    jd = "Hiring Python engineer with FastAPI and Docker"
    ranked = matcher.rank(jd_text=jd, k=10)
    assert ranked and ranked[0].cv_id == "cv_best"

    evidence = matcher.evidence_chunks(jd_text=jd, cv_id="cv_best", k=20, top_n=2)
    assert evidence

    review = review_with_llama3(cv_id="cv_best", jd_text=jd, evidence_chunks=evidence, settings=settings)
    assert 0 <= review.score <= 100
    assert isinstance(review.summary, str)
