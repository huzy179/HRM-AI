from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.worker.queue import enqueue_job
from backend.services.policy_rag import PolicyRAG
from backend.api.upload_limits import ensure_file_count, save_upload_limited


router = APIRouter()


class PolicyChatIn(BaseModel):
    query: str
    k: int = 5


class PolicyChatOut(BaseModel):
    answer: str
    citations: list[dict]


@router.post("/ingest")
async def ingest_policy(session: SessionDep, files: List[UploadFile] = File(...)) -> dict:
    uploads_dir = Path("uploads") / "policy"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ensure_file_count(len(files))
    doc_ids: list[int] = []
    for f in files:
        dest = uploads_dir / f.filename
        await save_upload_limited(f, dest)
        doc = models.PolicyDocument(filename=f.filename, file_path=str(dest), ingest_status="PENDING")
        session.add(doc)
        session.flush()
        doc_ids.append(doc.id)

    session.commit()
    job_id = enqueue_job("policy_ingest", {"doc_ids": doc_ids})
    return {"ok": True, "doc_ids": doc_ids, "job_id": job_id}


@router.post("/chat", response_model=PolicyChatOut)
def chat_policy(payload: PolicyChatIn) -> PolicyChatOut:
    rag = PolicyRAG()
    ans = rag.answer(query=payload.query, k=payload.k)
    return PolicyChatOut(
        answer=ans.answer,
        citations=[{"source": c.source, "chunk_id": c.chunk_id, "score": c.score, "snippet": c.snippet} for c in ans.citations],
    )
