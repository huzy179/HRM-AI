from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.worker.queue import enqueue_job
from backend.services.policy_rag import PolicyRAG
from backend.api.upload_limits import ensure_file_count, save_upload_limited
from backend.api.file_storage import unique_dest
from backend.core.tenant import current_tenant_id


router = APIRouter()


class PolicyChatIn(BaseModel):
    query: str
    k: int = 5


class PolicyChatOut(BaseModel):
    answer: str
    citations: list[dict]

class PolicyDocumentOut(BaseModel):
    id: int
    filename: str
    ingest_status: str
    ingest_method: str
    error: str | None = None


@router.post("/ingest")
async def ingest_policy(session: SessionDep, files: List[UploadFile] = File(...)) -> dict:
    tenant_id = current_tenant_id()
    uploads_dir = Path("uploads") / "policy"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ensure_file_count(len(files))
    doc_ids: list[int] = []
    for f in files:
        dest = unique_dest(uploads_dir, f.filename)
        await save_upload_limited(f, dest)
        doc = models.PolicyDocument(tenant_id=tenant_id, filename=f.filename, file_path=str(dest), ingest_status="PENDING")
        session.add(doc)
        session.flush()
        doc_ids.append(doc.id)

    session.commit()
    job_id = enqueue_job("policy_ingest", {"doc_ids": doc_ids})
    return {"ok": True, "doc_ids": doc_ids, "job_id": job_id}


@router.get("/documents", response_model=list[PolicyDocumentOut])
def list_policy_documents(session: SessionDep, limit: int = 200) -> list[PolicyDocumentOut]:
    tenant_id = current_tenant_id()
    limit = max(1, min(1000, int(limit)))
    rows = (
        session.query(models.PolicyDocument)
        .filter(models.PolicyDocument.tenant_id == tenant_id)
        .order_by(models.PolicyDocument.id.desc())
        .limit(limit)
        .all()
    )
    return [
        PolicyDocumentOut(
            id=r.id,
            filename=r.filename,
            ingest_status=r.ingest_status,
            ingest_method=getattr(r, "ingest_method", "unknown") or "unknown",
            error=r.error,
        )
        for r in rows
    ]


@router.post("/chat", response_model=PolicyChatOut)
def chat_policy(payload: PolicyChatIn) -> PolicyChatOut:
    rag = PolicyRAG()
    ans = rag.answer(query=payload.query, k=payload.k)
    return PolicyChatOut(
        answer=ans.answer,
        citations=[{"source": c.source, "chunk_id": c.chunk_id, "score": c.score, "snippet": c.snippet} for c in ans.citations],
    )


@router.post("/clear")
def clear_policy_index(confirm: bool = False) -> dict:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear policy index")
    job_id = enqueue_job("policy_clear", {})
    return {"ok": True, "job_id": job_id}


@router.post("/rebuild")
def rebuild_policy_index(confirm: bool = False) -> dict:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to rebuild policy index")
    job_id = enqueue_job("policy_rebuild", {})
    return {"ok": True, "job_id": job_id}
