from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import time

from backend.db.session import SessionLocal
from backend.db import models
from backend.services.cv_parser import parse_file
from backend.services.matcher import CVMatcher
from backend.core.config import settings_for_campaign
from backend.services.llm_scorer import review_with_llama3
from backend.services.policy_rag import PolicyRAG
from backend.services.text_quality import assess_text_quality
from backend.services.profile_extractor import extract_candidate_profile

logger = logging.getLogger(__name__)


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
    start = time.time()
    _update_job(job_id, status="RUNNING", progress=0, error=None)
    logger.info("job.start job_id=%s type=%s payload_keys=%s", job_id, job_type, sorted(payload.keys()))
    try:
        if job_type == "parse_jd":
            _parse_jd(payload["campaign_id"], job_id)
        elif job_type == "parse_cvs":
            _parse_cvs(payload["campaign_id"], job_id)
        elif job_type == "screen_campaign":
            _screen_campaign(payload["campaign_id"], job_id)
        elif job_type == "review_candidate":
            _review_candidate(payload["campaign_id"], payload["candidate_id"], job_id)
        elif job_type == "policy_ingest":
            _policy_ingest(payload.get("doc_ids") or [], job_id)
        elif job_type == "extract_profile":
            _extract_profile(payload["campaign_id"], payload["candidate_id"], job_id)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        _update_job(job_id, status="DONE", progress=100)
        logger.info("job.done job_id=%s type=%s duration_s=%.2f", job_id, job_type, time.time() - start)
    except Exception as exc:  # noqa: BLE001
        _update_job(job_id, status="FAILED", error=f"{exc.__class__.__name__}: {exc}")
        logger.exception("job.failed job_id=%s type=%s duration_s=%.2f", job_id, job_type, time.time() - start)
        raise


def _parse_jd(campaign_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        jd = session.query(models.JobDescription).filter(models.JobDescription.campaign_id == campaign_id).one()
        if jd.parse_status == "OK" and (jd.text or "").strip() and not (jd.error or "").strip():
            logger.info("parse_jd.skip campaign_id=%s reason=already_ok", campaign_id)
            _update_job(job_id, progress=100)
            return
        result = parse_file(jd.file_path)
        jd.text = result.raw_text
        jd.parse_status = "OK" if result.error is None else "ERROR"
        jd.parse_method = result.method
        jd.error = result.error
        if result.error is None and (result.raw_text or "").strip() and result.method.startswith("ocr_"):
            q = assess_text_quality(result.raw_text)
            if not q.ok:
                jd.parse_status = "ERROR"
                jd.error = f"OCR_LOW_QUALITY:{q.reason}"
                jd.text = None
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
            if cand.parse_status == "OK" and (cand.text or "").strip() and not (cand.error or "").strip():
                _update_job(job_id, progress=int((idx + 1) / total * 100))
                continue
            result = parse_file(cand.file_path)
            cand.text = result.raw_text
            cand.parse_method = result.method
            cand.parse_chars = len((result.raw_text or "").strip())

            if result.error is None and (result.raw_text or "").strip() and result.method.startswith("ocr_"):
                q = assess_text_quality(result.raw_text)
                cand.quality_score = float(q.score)
                cand.quality_reason = q.reason if not q.ok else ""
                if not q.ok:
                    cand.parse_status = "ERROR"
                    cand.error = f"OCR_LOW_QUALITY:{q.reason}"
                    cand.text = ""
                else:
                    cand.parse_status = "OK"
                    cand.error = None
            else:
                cand.quality_score = 0.0
                cand.quality_reason = ""
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

        settings = settings_for_campaign(campaign_id)
        matcher = CVMatcher(settings)
        matcher.reset_collection()

        for cand in ok_candidates:
            matcher.index_cv(cv_id=str(cand.id), cv_text=cand.text or "", metadata={"candidate_id": cand.id, "campaign_id": campaign_id})

        ranked = matcher.rank(jd_text=jd.text or "", k=50)

        session.query(models.ScreeningResult).filter(models.ScreeningResult.campaign_id == campaign_id).delete()
        session.commit()

        for r in ranked:
            cand_id = int(r.cv_id)
            evidence = matcher.evidence_chunks(jd_text=jd.text or "", cv_id=str(cand_id), k=80, top_n=3)
            session.add(
                models.ScreeningResult(
                    campaign_id=campaign_id,
                    candidate_id=cand_id,
                    score_embed=float(r.score),
                    notes=r.notes,
                    evidence_json=models.json_dumps(evidence),
                )
            )
        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)


def _review_candidate(campaign_id: int, candidate_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        jd = session.query(models.JobDescription).filter(models.JobDescription.campaign_id == campaign_id).one_or_none()
        cand = session.get(models.Candidate, candidate_id)
        if jd is None or not (jd.text or "").strip():
            raise RuntimeError("JD_NOT_READY")
        if cand is None or cand.campaign_id != campaign_id:
            raise RuntimeError("CANDIDATE_NOT_FOUND")
        if cand.parse_status != "OK" or not (cand.text or "").strip():
            raise RuntimeError("CANDIDATE_TEXT_NOT_READY")

        existing = (
            session.query(models.ReviewResult)
            .filter(models.ReviewResult.campaign_id == campaign_id, models.ReviewResult.candidate_id == candidate_id)
            .one_or_none()
        )
        if existing is not None and (existing.summary or "").strip():
            logger.info("review_candidate.skip campaign_id=%s candidate_id=%s reason=already_done", campaign_id, candidate_id)
            _update_job(job_id, progress=100)
            return

        settings = settings_for_campaign(campaign_id)
        matcher = CVMatcher(settings)
        evidence = matcher.evidence_chunks(jd_text=jd.text or "", cv_id=str(candidate_id), k=80, top_n=3)
        review = review_with_llama3(cv_id=str(candidate_id), jd_text=jd.text or "", evidence_chunks=evidence, settings=settings)

        if existing is None:
            existing = models.ReviewResult(campaign_id=campaign_id, candidate_id=candidate_id)
            session.add(existing)

        existing.score_llm = int(review.score)
        existing.summary = review.summary
        existing.strengths_json = models.json_dumps(review.strengths)
        existing.gaps_json = models.json_dumps(review.gaps)
        existing.evidence_json = models.json_dumps(review.evidence)
        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)


def _policy_ingest(doc_ids: list[int], job_id: str) -> None:
    session = SessionLocal()
    try:
        if doc_ids:
            pending = (
                session.query(models.PolicyDocument)
                .filter(models.PolicyDocument.id.in_(doc_ids))
                .order_by(models.PolicyDocument.id.asc())
                .all()
            )
        else:
            pending = (
                session.query(models.PolicyDocument)
                .filter(models.PolicyDocument.ingest_status == "PENDING")
                .order_by(models.PolicyDocument.id.asc())
                .all()
            )
        total = max(len(pending), 1)
        rag = PolicyRAG()
        for idx, doc in enumerate(pending):
            # mark running
            doc.ingest_status = "RUNNING"
            doc.error = None
            session.commit()

            result = parse_file(doc.file_path)
            doc.text = result.raw_text
            doc.ingest_status = "OK" if result.error is None else "ERROR"
            doc.ingest_method = result.method
            doc.error = result.error
            session.commit()

            if doc.ingest_status == "OK" and (doc.text or "").strip() and result.method.startswith("ocr_"):
                q = assess_text_quality(doc.text or "")
                if not q.ok:
                    doc.ingest_status = "ERROR"
                    doc.error = f"OCR_LOW_QUALITY:{q.reason}"
                    doc.text = None
                    session.commit()

            if doc.ingest_status == "OK" and (doc.text or "").strip():
                rag.ingest_text(doc_id=str(doc.id), source=doc.filename, text=doc.text or "")
            _update_job(job_id, progress=int((idx + 1) / total * 100))
    finally:
        session.close()


def _extract_profile(campaign_id: int, candidate_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        cand = session.get(models.Candidate, candidate_id)
        if cand is None or cand.campaign_id != campaign_id:
            raise RuntimeError("CANDIDATE_NOT_FOUND")
        if cand.parse_status != "OK" or not (cand.text or "").strip():
            raise RuntimeError("CANDIDATE_TEXT_NOT_READY")

        extracted = extract_candidate_profile(cand.text or "")

        existing = (
            session.query(models.CandidateProfile)
            .filter(models.CandidateProfile.candidate_id == candidate_id)
            .one_or_none()
        )
        if existing is None:
            existing = models.CandidateProfile(candidate_id=candidate_id)
            session.add(existing)

        existing.name = extracted.name
        existing.email = extracted.email
        existing.phone = extracted.phone
        existing.years_experience = float(extracted.years_experience or 0.0)
        existing.education = extracted.education
        existing.skills_json = models.json_dumps(extracted.skills or [])
        existing.updated_at = datetime.utcnow()

        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)
