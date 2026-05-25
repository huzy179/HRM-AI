from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import time

from backend.db.session import SessionLocal
from backend.db import models
from backend.services.cv_parser import parse_file
from backend.services.matcher import CVMatcher
from backend.core.config import get_settings, settings_for_campaign
from backend.services.llm_scorer import review_with_llama3
from backend.services.policy_rag import PolicyRAG
from backend.services.text_quality import assess_text_quality
from backend.services.profile_extractor import extract_candidate_profile
from backend.services.composite_scorer import combine_scores, score_candidate_rules
from backend.services.hashing import sha256_text, sha256_hex
from backend.services.storage_cleanup import cleanup_storage

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


def _set_job_result(job_id: str, result_json: str) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.Job, job_id)
        if job is None:
            return
        job.result_json = result_json or ""
        job.updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()

def run_job(job_type: str, payload: dict, job_id: str) -> None:
    start = time.time()
    _update_job(job_id, status="RUNNING", progress=0, error=None)
    _mark_job_started(job_id)
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
        elif job_type == "policy_rebuild":
            _policy_rebuild(job_id)
        elif job_type == "policy_clear":
            _policy_clear(job_id)
        elif job_type == "extract_profile":
            _extract_profile(payload["campaign_id"], payload["candidate_id"], job_id)
        elif job_type == "cleanup_storage":
            _cleanup_storage(payload, job_id)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # persist metrics
        _mark_job_finished(job_id, started_ts=start)
        _update_job(job_id, status="DONE", progress=100)
        logger.info("job.done job_id=%s type=%s duration_s=%.2f", job_id, job_type, time.time() - start)
    except Exception as exc:  # noqa: BLE001
        _mark_job_finished(job_id, started_ts=start, failed=True)
        _update_job(job_id, status="FAILED", error=f"{exc.__class__.__name__}: {exc}")
        logger.exception("job.failed job_id=%s type=%s duration_s=%.2f", job_id, job_type, time.time() - start)
        raise


def _mark_job_finished(job_id: str, *, started_ts: float, failed: bool = False) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.Job, job_id)
        if job is None:
            return
        now = datetime.utcnow()
        if job.started_at is None:
            job.started_at = now
        job.finished_at = now
        duration_ms = int(max(0.0, (time.time() - started_ts)) * 1000)
        job.duration_ms = duration_ms
        if failed and not (job.error or "").strip():
            job.error = "FAILED"
        job.updated_at = now
        session.commit()
    finally:
        session.close()


def _mark_job_started(job_id: str) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.Job, job_id)
        if job is None:
            return
        now = datetime.utcnow()
        if job.started_at is None:
            job.started_at = now
        job.updated_at = now
        session.commit()
    finally:
        session.close()


def _parse_jd(campaign_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        jd = (
            session.query(models.JobDescription)
            .filter(models.JobDescription.campaign_id == campaign_id, models.JobDescription.tenant_id == tenant_id)
            .one()
        )
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
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        candidates = (
            session.query(models.Candidate)
            .filter(models.Candidate.campaign_id == campaign_id, models.Candidate.tenant_id == tenant_id)
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
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        jd = (
            session.query(models.JobDescription)
            .filter(models.JobDescription.campaign_id == campaign_id, models.JobDescription.tenant_id == tenant_id)
            .one_or_none()
        )
        if jd is None or not (jd.text or "").strip():
            raise RuntimeError("JD_NOT_READY")

        candidates = (
            session.query(models.Candidate)
            .filter(models.Candidate.campaign_id == campaign_id, models.Candidate.tenant_id == tenant_id)
            .order_by(models.Candidate.id.asc())
            .all()
        )
        ok_candidates = [c for c in candidates if (c.parse_status == "OK") and (c.text or "").strip()]

        settings = settings_for_campaign(campaign_id)
        matcher = CVMatcher(settings)

        camp_settings = (
            session.query(models.CampaignSettings)
            .filter(models.CampaignSettings.campaign_id == campaign_id, models.CampaignSettings.tenant_id == tenant_id)
            .one_or_none()
        )
        w_embed = float(getattr(camp_settings, "w_embed", 0.7) or 0.7)
        import json

        required_skills_override: list[str] | None = None
        min_years_override: float | None = None
        if camp_settings is not None:
            try:
                obj = json.loads(getattr(camp_settings, "required_skills_json", "[]") or "[]")
                if isinstance(obj, list) and obj:
                    required_skills_override = [str(x).strip().lower() for x in obj if str(x).strip()]
            except Exception:
                required_skills_override = None
            min_years_override = float(getattr(camp_settings, "min_years_override", 0.0) or 0.0) or None

        # Compute deterministic run hash for idempotency
        parts: list[bytes] = []
        parts.append(b"campaign:" + str(campaign_id).encode("utf-8"))
        parts.append(b"jd:" + sha256_text(jd.text or "").encode("utf-8"))
        parts.append(b"w_embed:" + str(round(float(w_embed), 4)).encode("utf-8"))
        parts.append(b"min_years:" + str(float(min_years_override or 0.0)).encode("utf-8"))
        parts.append(b"skills:" + ",".join(sorted(required_skills_override or [])).encode("utf-8"))
        for cand in ok_candidates:
            parts.append(b"cand:" + str(cand.id).encode("utf-8") + b":" + sha256_text(cand.text or "").encode("utf-8"))
        run_hash = sha256_hex(b"\n".join(parts))

        # Skip if DB already has same run_hash and Chroma index directory exists
        chroma_ready = False
        try:
            if settings.chroma_cv_screening_dir.exists():
                chroma_ready = any(settings.chroma_cv_screening_dir.rglob("*"))
        except Exception:
            chroma_ready = False

        if chroma_ready:
            existing = (
                session.query(models.ScreeningResult)
                .filter(
                    models.ScreeningResult.campaign_id == campaign_id,
                    models.ScreeningResult.tenant_id == tenant_id,
                    models.ScreeningResult.run_hash == run_hash,
                )
                .count()
            )
            if existing >= len(ok_candidates) and len(ok_candidates) > 0:
                logger.info("screen_campaign.skip campaign_id=%s reason=same_run_hash candidates=%s", campaign_id, len(ok_candidates))
                _update_job(job_id, progress=100)
                return

        matcher.reset_collection()
        for cand in ok_candidates:
            matcher.index_cv(cv_id=str(cand.id), cv_text=cand.text or "", metadata={"candidate_id": cand.id, "campaign_id": campaign_id})

        ranked = matcher.rank(jd_text=jd.text or "", k=50)

        session.query(models.ScreeningResult).filter(
            models.ScreeningResult.campaign_id == campaign_id,
            models.ScreeningResult.tenant_id == tenant_id,
        ).delete()
        session.commit()

        for r in ranked:
            cand_id = int(r.cv_id)
            evidence = matcher.evidence_chunks(jd_text=jd.text or "", cv_id=str(cand_id), k=80, top_n=3)
            profile = (
                session.query(models.CandidateProfile)
                .filter(models.CandidateProfile.candidate_id == cand_id)
                .one_or_none()
            )
            rule = score_candidate_rules(
                jd_text=jd.text or "",
                profile=profile,
                required_skills_override=required_skills_override,
                min_years_override=min_years_override,
            )
            total = combine_scores(embed_score=float(r.score), rules_score=float(rule.score), w_embed=w_embed)
            session.add(
                models.ScreeningResult(
                    campaign_id=campaign_id,
                    candidate_id=cand_id,
                    tenant_id=tenant_id,
                    score_embed=float(r.score),
                    score_rules=float(rule.score),
                    score_total=float(total),
                    notes=r.notes,
                    evidence_json=models.json_dumps(evidence),
                    rules_json=models.json_dumps(rule.details),
                    run_hash=run_hash,
                )
            )
        session.commit()
    finally:
        session.close()
    _update_job(job_id, progress=100)


def _review_candidate(campaign_id: int, candidate_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        jd = (
            session.query(models.JobDescription)
            .filter(models.JobDescription.campaign_id == campaign_id, models.JobDescription.tenant_id == tenant_id)
            .one_or_none()
        )
        cand = session.get(models.Candidate, candidate_id)
        if jd is None or not (jd.text or "").strip():
            raise RuntimeError("JD_NOT_READY")
        if cand is None or cand.tenant_id != tenant_id or cand.campaign_id != campaign_id:
            raise RuntimeError("CANDIDATE_NOT_FOUND")
        if cand.parse_status != "OK" or not (cand.text or "").strip():
            raise RuntimeError("CANDIDATE_TEXT_NOT_READY")

        existing = (
            session.query(models.ReviewResult)
            .filter(
                models.ReviewResult.campaign_id == campaign_id,
                models.ReviewResult.candidate_id == candidate_id,
                models.ReviewResult.tenant_id == tenant_id,
            )
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
            existing = models.ReviewResult(campaign_id=campaign_id, candidate_id=candidate_id, tenant_id=tenant_id)
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
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        if doc_ids:
            pending = (
                session.query(models.PolicyDocument)
                .filter(models.PolicyDocument.id.in_(doc_ids), models.PolicyDocument.tenant_id == tenant_id)
                .order_by(models.PolicyDocument.id.asc())
                .all()
            )
        else:
            pending = (
                session.query(models.PolicyDocument)
                .filter(models.PolicyDocument.ingest_status == "PENDING", models.PolicyDocument.tenant_id == tenant_id)
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


def _policy_clear(job_id: str) -> None:
    rag = PolicyRAG()
    rag.reset_collection()
    _update_job(job_id, progress=100)


def _policy_rebuild(job_id: str) -> None:
    session = SessionLocal()
    try:
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        docs = (
            session.query(models.PolicyDocument)
            .filter(models.PolicyDocument.ingest_status == "OK", models.PolicyDocument.tenant_id == tenant_id)
            .order_by(models.PolicyDocument.id.asc())
            .all()
        )
        rag = PolicyRAG()
        rag.reset_collection()
        total = max(len(docs), 1)
        for idx, doc in enumerate(docs):
            if not (doc.text or "").strip():
                continue
            rag.ingest_text(doc_id=str(doc.id), source=doc.filename, text=doc.text or "")
            _update_job(job_id, progress=int((idx + 1) / total * 100))
    finally:
        session.close()
    _update_job(job_id, progress=100)


def _extract_profile(campaign_id: int, candidate_id: int, job_id: str) -> None:
    session = SessionLocal()
    try:
        tenant_id = session.get(models.Job, job_id).tenant_id if session.get(models.Job, job_id) else "default"
        cand = session.get(models.Candidate, candidate_id)
        if cand is None or cand.tenant_id != tenant_id or cand.campaign_id != campaign_id:
            raise RuntimeError("CANDIDATE_NOT_FOUND")
        if cand.parse_status != "OK" or not (cand.text or "").strip():
            raise RuntimeError("CANDIDATE_TEXT_NOT_READY")

        extracted = extract_candidate_profile(cand.text or "")

        existing = (
            session.query(models.CandidateProfile)
            .filter(models.CandidateProfile.candidate_id == candidate_id, models.CandidateProfile.tenant_id == tenant_id)
            .one_or_none()
        )
        if existing is None:
            existing = models.CandidateProfile(candidate_id=candidate_id, tenant_id=tenant_id)
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


def _cleanup_storage(payload: dict, job_id: str) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.Job, job_id)
        tenant_id = getattr(job, "tenant_id", "default") if job else "default"
        dry_run = bool(payload.get("dry_run", True))

        referenced_files: set[str] = set()
        referenced_campaign_ids: set[int] = set()

        # campaigns in tenant
        for c in session.query(models.Campaign).filter(models.Campaign.tenant_id == tenant_id).all():
            referenced_campaign_ids.add(int(c.id))

        # referenced file paths for tenant
        for jd in session.query(models.JobDescription).filter(models.JobDescription.tenant_id == tenant_id).all():
            if jd.file_path:
                referenced_files.add(str(jd.file_path))
        for cand in session.query(models.Candidate).filter(models.Candidate.tenant_id == tenant_id).all():
            if cand.file_path:
                referenced_files.add(str(cand.file_path))
        for doc in session.query(models.PolicyDocument).filter(models.PolicyDocument.tenant_id == tenant_id).all():
            if doc.file_path:
                referenced_files.add(str(doc.file_path))

        root = Path(get_settings().project_root)
        uploads_root = root / "uploads"
        chroma_root = root / "data" / "chroma_db"

        def _abs_path(p: str) -> str:
            pp = Path(p)
            if pp.is_absolute():
                return str(pp)
            return str((root / pp).resolve())

        referenced_files_abs = {_abs_path(p) for p in referenced_files}

        report = cleanup_storage(
            tenant_id=tenant_id,
            uploads_root=uploads_root,
            chroma_root=chroma_root,
            referenced_files=referenced_files_abs,
            referenced_campaign_ids=referenced_campaign_ids,
            dry_run=dry_run,
        )
        _set_job_result(job_id, models.json_dumps(report.__dict__))
        _update_job(job_id, progress=100)
    finally:
        session.close()
