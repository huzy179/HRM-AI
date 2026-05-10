from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import Settings, ensure_dirs, get_settings
from backend.services.utils import normalize_text


@dataclass(frozen=True)
class PolicyCitation:
    source: str
    chunk_id: int
    score: float
    snippet: str


@dataclass(frozen=True)
class PolicyAnswer:
    answer: str
    citations: List[PolicyCitation]


class PolicyRAG:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        ensure_dirs(self.settings)

        self.embeddings = OllamaEmbeddings(
            model=self.settings.ollama_embed_model,
            base_url=self.settings.ollama_base_url,
        )
        policy_dir = self.settings.chroma_dir / "policy"
        policy_dir.mkdir(parents=True, exist_ok=True)
        self.store = Chroma(
            collection_name="policy_docs",
            embedding_function=self.embeddings,
            persist_directory=str(policy_dir),
        )
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)

        self.llm = ChatOllama(
            model=self.settings.ollama_chat_model,
            base_url=self.settings.ollama_base_url,
            temperature=0,
        )

    def ingest_text(self, *, doc_id: str, source: str, text: str) -> int:
        cleaned = normalize_text(text)
        chunks = [c for c in self.splitter.split_text(cleaned) if c.strip()]
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        for i, chunk in enumerate(chunks):
            metadatas.append({"doc_id": doc_id, "source": source, "chunk_id": i})
            ids.append(f"{doc_id}::chunk_{i}")
        if chunks:
            self.store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
        return len(chunks)

    def retrieve(self, *, query: str, k: int = 5) -> List[PolicyCitation]:
        q = normalize_text(query)
        hits = self.store.similarity_search_with_score(q, k=k)
        citations: List[PolicyCitation] = []
        for doc, distance in hits:
            meta = dict(doc.metadata or {})
            source = str(meta.get("source") or "")
            chunk_id = int(meta.get("chunk_id") or 0)
            similarity = 1.0 / (1.0 + float(distance))
            snippet = (doc.page_content or "").strip()[:400]
            citations.append(PolicyCitation(source=source, chunk_id=chunk_id, score=similarity, snippet=snippet))
        return citations

    def answer(self, *, query: str, k: int = 5) -> PolicyAnswer:
        citations = self.retrieve(query=query, k=k)
        context = "\n\n---\n\n".join(
            f"SOURCE: {c.source} | CHUNK: {c.chunk_id}\n{c.snippet}" for c in citations
        )

        prompt = (
            "Bạn là trợ lý HR trả lời dựa trên tài liệu nội bộ.\n"
            "Chỉ dùng thông tin trong CONTEXT. Nếu không đủ thông tin, trả lời: \"Không tìm thấy trong tài liệu\".\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{query.strip()}\n\n"
            "Trả lời ngắn gọn, rõ ràng."
        )
        resp = self.llm.invoke(prompt)
        text = (getattr(resp, "content", "") or "").strip()
        return PolicyAnswer(answer=text, citations=citations)

