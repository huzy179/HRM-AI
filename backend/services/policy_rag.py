from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import Settings, ensure_dirs, get_settings
from backend.services.ollama_utils import invoke_with_retry
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
            client_kwargs={"timeout": self.settings.ollama_timeout_s},
        )
        tenant = (getattr(self.settings, "tenant_id", None) or "default").strip() or "default"
        policy_dir = self.settings.chroma_dir / f"policy_{tenant}"
        policy_dir.mkdir(parents=True, exist_ok=True)
        self.store = Chroma(
            collection_name=f"policy_docs_{tenant}",
            embedding_function=self.embeddings,
            persist_directory=str(policy_dir),
        )
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)

        self.llm = ChatOllama(
            model=self.settings.ollama_chat_model,
            base_url=self.settings.ollama_base_url,
            temperature=0,
            client_kwargs={"timeout": self.settings.ollama_timeout_s},
        )

    def reset_collection(self) -> None:
        """
        Clear policy collection for current tenant.
        """
        try:
            self.store.delete_collection()
        except Exception:
            pass

        tenant = (getattr(self.settings, "tenant_id", None) or "default").strip() or "default"
        policy_dir = self.settings.chroma_dir / f"policy_{tenant}"
        policy_dir.mkdir(parents=True, exist_ok=True)
        self.store = Chroma(
            collection_name=f"policy_docs_{tenant}",
            embedding_function=self.embeddings,
            persist_directory=str(policy_dir),
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

    def retrieve(self, *, query: str, k: int = 5, doc_ids: list[str] | None = None) -> List[PolicyCitation]:
        q = normalize_text(query)
        # Query k * 3 candidates for reranking pool
        candidates_k = k * 3
        
        search_filter = None
        if doc_ids:
            cleaned_ids = [str(x).strip() for x in doc_ids if str(x).strip()]
            if len(cleaned_ids) == 1:
                search_filter = {"doc_id": cleaned_ids[0]}
            elif len(cleaned_ids) > 1:
                search_filter = {"doc_id": {"$in": cleaned_ids}}

        hits = self.store.similarity_search_with_score(q, k=candidates_k, filter=search_filter)
        
        citations: List[PolicyCitation] = []
        for doc, distance in hits:
            meta = dict(doc.metadata or {})
            source = str(meta.get("source") or "")
            chunk_id = int(meta.get("chunk_id") or 0)
            similarity = 1.0 / (1.0 + float(distance))
            snippet = (doc.page_content or "").strip()[:400]
            citations.append(PolicyCitation(source=source, chunk_id=chunk_id, score=similarity, snippet=snippet))
            
        # Hybrid Keyword Reranker: calculate token overlap ratio and compute a hybrid score
        q_tokens = set(q.lower().split())
        if q_tokens:
            reranked_citations: List[PolicyCitation] = []
            for c in citations:
                c_tokens = set(c.snippet.lower().split())
                overlap = len(q_tokens.intersection(c_tokens)) / len(q_tokens) if q_tokens else 0.0
                # Hybrid score = 0.6 * dense_similarity + 0.4 * sparse_keyword_overlap
                hybrid_score = 0.6 * c.score + 0.4 * overlap
                reranked_citations.append(
                    PolicyCitation(
                        source=c.source,
                        chunk_id=c.chunk_id,
                        score=hybrid_score,
                        snippet=c.snippet
                    )
                )
            citations = reranked_citations
            
        # Sort and return top k
        citations.sort(key=lambda x: x.score, reverse=True)
        return citations[:k]

    def answer(self, *, query: str, k: int = 5, history: list[dict] | None = None, doc_ids: list[str] | None = None) -> PolicyAnswer:
        citations = self.retrieve(query=query, k=k, doc_ids=doc_ids)
        if not citations:
            return PolicyAnswer(answer="Không tìm thấy trong tài liệu", citations=[])
        context = "\n\n---\n\n".join(
            f"SOURCE: {c.source} | CHUNK: {c.chunk_id}\n{c.snippet}" for c in citations
        )

        history_str = ""
        if history:
            history_str = "LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:\n"
            for msg in history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_str += f"{role}: {msg.get('content')}\n"
            history_str += "\n"

        prompt = (
            "Bạn là trợ lý HR trả lời dựa trên tài liệu nội bộ.\n"
            "Chỉ dùng thông tin trong CONTEXT. Nếu không đủ thông tin, trả lời: \"Không tìm thấy trong tài liệu\".\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"{history_str}"
            f"QUESTION:\n{query.strip()}\n\n"
            "Trả lời ngắn gọn, rõ ràng."
        )
        resp = invoke_with_retry(
            self.llm,
            prompt,
            retries=self.settings.ollama_retries,
            backoff_s=self.settings.ollama_retry_backoff_s,
        )
        text = (getattr(resp, "content", "") or "").strip()
        return PolicyAnswer(answer=text, citations=citations)

    def stream_answer(self, *, query: str, k: int = 5, history: list[dict] | None = None, doc_ids: list[str] | None = None) -> Generator[str, None, None]:
        citations = self.retrieve(query=query, k=k, doc_ids=doc_ids)
        if not citations:
            yield "CITATIONS: []\n"
            yield "Không tìm thấy trong tài liệu"
            return

        # Yield citations first as a special prefix line
        import json
        citations_data = [{"source": c.source, "chunk_id": c.chunk_id, "score": c.score, "snippet": c.snippet} for c in citations]
        yield "CITATIONS: " + json.dumps(citations_data) + "\n"

        context = "\n\n---\n\n".join(
            f"SOURCE: {c.source} | CHUNK: {c.chunk_id}\n{c.snippet}" for c in citations
        )

        history_str = ""
        if history:
            history_str = "LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:\n"
            for msg in history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_str += f"{role}: {msg.get('content')}\n"
            history_str += "\n"

        prompt = (
            "Bạn là trợ lý HR trả lời dựa trên tài liệu nội bộ.\n"
            "Chỉ dùng thông tin trong CONTEXT. Nếu không đủ thông tin, trả lời: \"Không tìm thấy trong tài liệu\".\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"{history_str}"
            f"QUESTION:\n{query.strip()}\n\n"
            "Trả lời ngắn gọn, rõ ràng."
        )

        try:
            for chunk in self.llm.stream(prompt):
                content = getattr(chunk, "content", "") or ""
                if content:
                    yield content
        except Exception as e:
            yield f"\n[Lỗi kết nối Ollama: {e}]"
