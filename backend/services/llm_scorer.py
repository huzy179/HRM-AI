from __future__ import annotations

import json
from typing import List

from langchain_ollama import ChatOllama

from backend.core.config import Settings, get_settings
from backend.core.schemas import CVLLMReview


def _build_prompt(*, jd_text: str, evidence_chunks: List[str]) -> str:
    evidence_block = "\n\n---\n\n".join(
        f"CHUNK {i+1}:\n{chunk.strip()}" for i, chunk in enumerate(evidence_chunks) if chunk.strip()
    )

    return (
        "Bạn là HR reviewer. Hãy đánh giá mức độ phù hợp của ứng viên với Job Description.\n"
        "Chỉ dựa trên Job Description và các đoạn trích từ CV (evidence). Nếu thiếu thông tin thì nói rõ.\n\n"
        "Yêu cầu output: TRẢ VỀ JSON HỢP LỆ duy nhất (không markdown, không text ngoài JSON) theo schema:\n"
        '{ "score": 0-100, "summary": "1-3 câu", "strengths": ["..."], "gaps": ["..."] }\n'
        "Luôn phải có đủ 4 keys: score, summary, strengths, gaps.\n\n"
        "Job Description:\n"
        f"{jd_text.strip()}\n\n"
        "Evidence from CV:\n"
        f"{evidence_block}\n"
    )


def review_with_llama3(*, cv_id: str, jd_text: str, evidence_chunks: List[str], settings: Settings | None = None) -> CVLLMReview:
    s = settings or get_settings()
    llm = ChatOllama(
        model=s.ollama_chat_model,
        base_url=s.ollama_base_url,
        temperature=0,
        format="json",
    )

    prompt = _build_prompt(jd_text=jd_text, evidence_chunks=evidence_chunks)
    response = llm.invoke(prompt)
    content = (getattr(response, "content", "") or "").strip()

    try:
        data = json.loads(content)
    except Exception:
        # best-effort fallback: wrap raw text
        return CVLLMReview(
            cv_id=cv_id,
            score=0,
            summary="LLM trả về output không phải JSON. Hãy thử lại hoặc giảm độ dài evidence.",
            strengths=[],
            gaps=[content[:500]],
            evidence=evidence_chunks[:3],
        )

    score = int(max(0, min(100, data.get("score", 0) or 0)))
    summary = str(data.get("summary", "") or "").strip()
    strengths = [str(x).strip() for x in (data.get("strengths") or []) if str(x).strip()]
    gaps = [str(x).strip() for x in (data.get("gaps") or []) if str(x).strip()]

    return CVLLMReview(
        cv_id=cv_id,
        score=score,
        summary=summary,
        strengths=strengths[:10],
        gaps=gaps[:10],
        evidence=evidence_chunks[:3],
    )
