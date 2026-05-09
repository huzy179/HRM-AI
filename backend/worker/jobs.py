from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.db.session import SessionLocal
from backend.db import models
from backend.services.cv_parser import parse_cv
from backend.services.matcher import CVMatcher


def _update_job(job_id: str, *, status: str | None = None, progress: int | None = None, error: str | None = None) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.Job, job_id)
        if job is None:
            return
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if error is not None:
            job.error = error
        job.updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def run_job(job_type: str, payload: dict, job_id: str) -> None:
    _update_job(job_id, status="RUNNING", progress=0, error=None)
    try:
        if job_type == "parse_jd":
            _parse_jd(payload["campaign_id"], job_id)
        elif job_type == "parse_cvs":
            _parse_cvs(payload["campaign_id"], job_id)
        elif job_type == "screen_campaign":
            _screen_campaign(payload["campaign_id"], job_id)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        _update_job(job_id, status="DONE", progress=100)
    except Exception as exc:  # noqa: BLE001
        _update_job(job_id, status="FAILED", error=f"{exc.__class__.__name__}: {exc}")
        raise


def _parse_jd(campaign_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        jd = session.query(models.JobDescription).filter(models.JobDescription.campaign_id == campaign_id).one()
        result = parse_cv(jd.file_path)
        jd.text = result.raw_text
        jd.parse_status = "OK" if result.error is None else "ERROR"
        jd.error = result.error
        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)


def _parse_cvs(campaign_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        candidates = (
            session.query(models.Candidate)
            .filter(models.Candidate.campaign_id == campaign_id)
            .order_by(models.Candidate.id.asc())
            .all()
        )
        total = max(len(candidates), 1)
        for idx, cand in enumerate(candidates):
            result = parse_cv(cand.file_path)
            cand.text = result.raw_text
            cand.parse_status = "OK" if result.error is None else "ERROR"
            cand.error = result.error
            session.commit()
            _update_job(job_id, progress=int((idx + 1) / total * 100))
    finally:
        session.close()


def _screen_campaign(campaign_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        jd = session.query(models.JobDescription).filter(models.JobDescription.campaign_id == campaign_id).one_or_none()
        if jd is None or not (jd.text or "").strip():
            raise RuntimeError("JD_NOT_READY")

        candidates = (
            session.query(models.Candidate)
            .filter(models.Candidate.campaign_id == campaign_id)
            .order_by(models.Candidate.id.asc())
            .all()
        )
        ok_candidates = [c for c in candidates if (c.parse_status == "OK") and (c.text or "").strip()]

        # Phase 2 simplification: reuse existing matcher but isolate per-campaign in its own chroma dir
        matcher = CVMatcher()
        matcher.reset_collection()

        for cand in ok_candidates:
            matcher.index_cv(cv_id=str(cand.id), cv_text=cand.text or "", metadata={"candidate_id": cand.id, "campaign_id": campaign_id})

        ranked = matcher.rank(jd_text=jd.text or "", k=50)

        session.query(models.ScreeningResult).filter(models.ScreeningResult.campaign_id == campaign_id).delete()
        session.commit()

        for r in ranked:
            cand_id = int(r.cv_id)
            session.add(
                models.ScreeningResult(
                    campaign_id=campaign_id,
                    candidate_id=cand_id,
                    score_embed=float(r.score),
                    notes=r.notes,
                )
            )
        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)

