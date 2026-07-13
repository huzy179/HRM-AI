from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.api.security import require_admin
from backend.core.tenant import current_tenant_id
from backend.db import models
from backend.db.session import SessionDep
from backend.worker.queue import enqueue_job


router = APIRouter()


class PolicyEvalQuestionIn(BaseModel):
    question: str
    expected_source: str = ""
    expected_keywords: list[str] = []


class PolicyEvalRunIn(BaseModel):
    name: str = "Policy eval"
    questions: list[PolicyEvalQuestionIn] | None = None


class PolicyEvalRunOut(BaseModel):
    id: int
    name: str
    status: str
    total_questions: int
    passed_questions: int
    score: float
    error: str | None = None
    created_at: str
    finished_at: str | None = None


class PolicyEvalItemOut(BaseModel):
    id: int
    question: str
    expected_source: str
    expected_keywords: list[str]
    answer: str
    citations: list[dict]
    passed: bool
    score: float
    notes: str


class PolicyEvalRunDetailOut(PolicyEvalRunOut):
    items: list[PolicyEvalItemOut]


def _default_questions() -> list[PolicyEvalQuestionIn]:
    return [
        PolicyEvalQuestionIn(
            question="Nhân viên chính thức có bao nhiêu ngày phép năm?",
            expected_source="policy_benefits_leave_2026.pdf",
            expected_keywords=["12 ngày phép"],
        ),
        PolicyEvalQuestionIn(
            question="Phụ cấp ăn trưa và gửi xe là bao nhiêu?",
            expected_source="policy_benefits_leave_2026.pdf",
            expected_keywords=["500.000", "150.000"],
        ),
        PolicyEvalQuestionIn(
            question="Giờ làm việc chính thức bắt đầu và kết thúc lúc nào?",
            expected_source="policy_working_rules_2026.pdf",
            expected_keywords=["08:30", "17:30"],
        ),
        PolicyEvalQuestionIn(
            question="Nhân viên được làm việc từ xa tối đa mấy ngày mỗi tuần?",
            expected_source="policy_remote_work_2026.pdf",
            expected_keywords=["2 ngày"],
        ),
        PolicyEvalQuestionIn(
            question="Ngân sách đào tạo cá nhân mỗi năm là bao nhiêu?",
            expected_source="policy_expense_training_2026.pdf",
            expected_keywords=["6.000.000"],
        ),
    ]


def _run_out(row: models.PolicyEvalRun) -> PolicyEvalRunOut:
    return PolicyEvalRunOut(
        id=row.id,
        name=row.name,
        status=row.status,
        total_questions=int(row.total_questions or 0),
        passed_questions=int(row.passed_questions or 0),
        score=float(row.score or 0.0),
        error=row.error,
        created_at=row.created_at.isoformat(),
        finished_at=row.finished_at.isoformat() if row.finished_at else None,
    )


@router.post("/runs")
def create_eval_run(payload: PolicyEvalRunIn, request: Request, session: SessionDep) -> dict:
    require_admin(request)
    tenant_id = current_tenant_id()
    questions = payload.questions if payload.questions is not None else _default_questions()
    questions = [q for q in questions if q.question.strip()]
    if not questions:
        raise HTTPException(status_code=400, detail="No eval questions provided")

    run = models.PolicyEvalRun(
        tenant_id=tenant_id,
        name=payload.name.strip() or "Policy eval",
        status="PENDING",
        total_questions=len(questions),
    )
    session.add(run)
    session.flush()

    for q in questions:
        session.add(
            models.PolicyEvalItem(
                run_id=run.id,
                tenant_id=tenant_id,
                question=q.question.strip(),
                expected_source=q.expected_source.strip(),
                expected_keywords_json=models.json_dumps([x.strip().lower() for x in q.expected_keywords if x.strip()]),
            )
        )
    session.commit()

    job_id = enqueue_job("policy_eval", {"run_id": run.id}, tenant_id=tenant_id)
    return {"ok": True, "run_id": run.id, "job_id": job_id}


@router.get("/runs", response_model=list[PolicyEvalRunOut])
def list_eval_runs(session: SessionDep, limit: int = 50) -> list[PolicyEvalRunOut]:
    tenant_id = current_tenant_id()
    rows = (
        session.query(models.PolicyEvalRun)
        .filter(models.PolicyEvalRun.tenant_id == tenant_id)
        .order_by(models.PolicyEvalRun.id.desc())
        .limit(max(1, min(200, int(limit))))
        .all()
    )
    return [_run_out(row) for row in rows]


@router.get("/runs/{run_id}", response_model=PolicyEvalRunDetailOut)
def get_eval_run(run_id: int, session: SessionDep) -> PolicyEvalRunDetailOut:
    tenant_id = current_tenant_id()
    run = session.get(models.PolicyEvalRun, int(run_id))
    if run is None or run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Eval run not found")

    items = (
        session.query(models.PolicyEvalItem)
        .filter(models.PolicyEvalItem.run_id == run.id, models.PolicyEvalItem.tenant_id == tenant_id)
        .order_by(models.PolicyEvalItem.id.asc())
        .all()
    )
    base = _run_out(run).model_dump()
    base["items"] = [
        PolicyEvalItemOut(
            id=item.id,
            question=item.question,
            expected_source=item.expected_source,
            expected_keywords=json.loads(item.expected_keywords_json or "[]"),
            answer=item.answer,
            citations=json.loads(item.citations_json or "[]"),
            passed=bool(item.passed),
            score=float(item.score or 0.0),
            notes=item.notes,
        )
        for item in items
    ]
    return PolicyEvalRunDetailOut(**base)
