from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import Settings, ensure_dirs, get_settings
from backend.core.schemas import CVParseResult, CVRankResult
from backend.services.utils import normalize_text


@dataclass(frozen=True)
class MatchHit:
    cv_id: str
    score: float
    distance: float
    metadata: Dict[str, Any]


def _distance_to_similarity(distance: float) -> float:
    """
    Convert a non-negative distance into a similarity in [0, 1].
    This is a simple monotonic mapping for Phase 1.
    """
    if distance <= 0:
        return 1.0
    return 1.0 / (1.0 + float(distance))


class CVMatcher:
    """
    Phase 1 matcher:
    - Index CV texts into Chroma
    - Query Job Description text and rank candidates using Ollama embeddings
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        ensure_dirs(self.settings)

        self.embeddings = OllamaEmbeddings(
            model=self.settings.ollama_embed_model,
            base_url=self.settings.ollama_base_url,
        )
        self.store = Chroma(
            collection_name=self.settings.chroma_collection_cvs,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_cv_screening_dir),
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.cv_chunk_size,
            chunk_overlap=self.settings.cv_chunk_overlap,
        )

    def reset_collection(self) -> None:
        """
        Clear all indexed CVs in the current collection.
        Useful for demos/tests.
        """
        try:
            self.store.delete_collection()
        except Exception:
            pass

        self.store = Chroma(
            collection_name=self.settings.chroma_collection_cvs,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_cv_screening_dir),
        )

    def index_cv(self, *, cv_id: str, cv_text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        text = normalize_text(cv_text)
        chunks = [c for c in self.splitter.split_text(text) if c.strip()]
        if not chunks:
            chunks = [text]

        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        for idx, chunk in enumerate(chunks):
            metadatas.append({**(metadata or {}), "cv_id": cv_id, "chunk_id": idx})
            ids.append(f"{cv_id}::chunk_{idx}")

        self.store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)

    def index_cvs(self, cvs: Sequence[CVParseResult]) -> List[CVRankResult]:
        """
        Index a batch of CVParseResult. Returns a per-CV status list.
        """
        results: List[CVRankResult] = []
        for cv in cvs:
            if cv.error:
                results.append(CVRankResult(cv_id=cv.cv_id, score=0.0, status="ERROR", notes=cv.error))
                continue
            if not cv.raw_text.strip():
                results.append(CVRankResult(cv_id=cv.cv_id, score=0.0, status="ERROR", notes="EMPTY_TEXT"))
                continue
            self.index_cv(cv_id=cv.cv_id, cv_text=cv.raw_text, metadata={"filename": cv.cv_id})
            results.append(CVRankResult(cv_id=cv.cv_id, score=0.0, status="OK", notes="INDEXED"))
        return results

    def rank(self, *, jd_text: str, k: int = 20) -> List[CVRankResult]:
        """
        Rank indexed CVs against the given JD text.

        Returns:
        - list sorted by score DESC
        - score is in [0, 100]
        """
        query = normalize_text(jd_text)
        if not query:
            return []

        hits = self.store.similarity_search_with_score(query, k=k)

        best_by_id: Dict[str, MatchHit] = {}
        for doc, distance in hits:
            meta = dict(doc.metadata or {})
            cv_id = meta.get("cv_id")
            if not cv_id:
                continue

            similarity = _distance_to_similarity(float(distance))
            score = round(similarity * 100.0, 2)

            prev = best_by_id.get(cv_id)
            if prev is None or score > prev.score:
                best_by_id[cv_id] = MatchHit(
                    cv_id=cv_id,
                    score=score,
                    distance=float(distance),
                    metadata=meta,
                )

        ranked = [
            CVRankResult(
                cv_id=hit.cv_id,
                score=hit.score,
                status="OK",
                notes=f"distance={hit.distance:.4f}; chunk_id={hit.metadata.get('chunk_id')}",
                metadata=hit.metadata,
            )
            for hit in best_by_id.values()
        ]
        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked

    def evidence_chunks(self, *, jd_text: str, cv_id: str, k: int = 50, top_n: int = 3) -> List[str]:
        """
        Return top-N most similar chunks for a specific CV against the JD.
        """
        query = normalize_text(jd_text)
        if not query:
            return []

        hits = self.store.similarity_search_with_score(query, k=k)
        chunks: List[Tuple[float, str]] = []
        for doc, distance in hits:
            meta = dict(doc.metadata or {})
            if meta.get("cv_id") != cv_id:
                continue
            chunks.append((float(distance), doc.page_content or ""))

        chunks.sort(key=lambda x: x[0])  # smallest distance first
        return [c for _, c in chunks[:top_n] if c.strip()]


def load_jd_from_file(path: str | Path) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")
