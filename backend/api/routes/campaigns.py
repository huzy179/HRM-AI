from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.db.session import SessionDep
from backend.db import models
from backend.worker.queue import enqueue_job
from backend.api.upload_limits import ensure_file_count, read_limited


router = APIRouter()


class CampaignCreate(BaseModel):
    name: str


class CampaignOut(BaseModel):
    id: int
    name: str


class CandidateOut(BaseModel):
    id: int
    filename: str
    parse_status: str
    error: Optional[str] = None
    parse_method: str = "unknown"
    chars: int = 0
    quality_score: float = 0.0
    quality_reason: str = ""


class ReviewOut(BaseModel):
    candidate_id: int
    score: int
    summary: str
    strengths: list[str]
    gaps: list[str]
    evidence: list[str]


class CandidateProfileOut(BaseModel):
    candidate_id: int
    name: str
    email: str
    phone: str
    years_experience: float
    education: str
    skills: list[str]


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, session: SessionDep) -> CampaignOut:
    campaign = models.Campaign(name=payload.name)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut(id=campaign.id, name=campaign.name)


@router.get("", response_model=List[CampaignOut])
def list_campaigns(session: SessionDep) -> List[CampaignOut]:
    rows = session.query(models.Campaign).order_by(models.Campaign.id.desc()).all()
    return [CampaignOut(id=r.id, name=r.name) for r in rows]


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: int, session: SessionDep) -> CampaignOut:
    campaign = session.get(models.Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignOut(id=campaign.id, name=campaign.name)


@router.post("/{campaign_id}/jd")
async def upload_jd(campaign_id: int, session: SessionDep, file: UploadFile = File(...)) -> dict:
    campaign = session.get(models.Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    uploads_dir = Path("uploads") / f"campaign_{campaign_id}" / "jd"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / file.filename
    content = await read_limited(file)
    dest.write_bytes(content)

    jd = session.query(models.JobDescription).filter(models.JobDescription.campaign_id == campaign_id).one_or_none()
    if jd is None:
        jd = models.JobDescription(campaign_id=campaign_id, filename=file.filename, file_path=str(dest))
        session.add(jd)
    else:
        jd.filename = file.filename
        jd.file_path = str(dest)
        jd.text = None
        jd.parse_status = "PENDING"
        jd.error = None
    session.commit()

    job_id = enqueue_job("parse_jd", {"campaign_id": campaign_id})
    return {"ok": True, "job_id": job_id}


@router.post("/{campaign_id}/cvs")
async def upload_cvs(campaign_id: int, session: SessionDep, files: List[UploadFile] = File(...)) -> dict:
    campaign = session.get(models.Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    ensure_file_count(len(files))
    uploads_dir = Path("uploads") / f"campaign_{campaign_id}" / "cvs"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    created: List[int] = []
    for up in files:
        dest = uploads_dir / up.filename
        dest.write_bytes(await read_limited(up))
        cand = models.Candidate(
            campaign_id=campaign_id,
            filename=up.filename,
            file_path=str(dest),
            parse_status="PENDING",
        )
        session.add(cand)
        session.flush()
        created.append(cand.id)

    session.commit()

    job_id = enqueue_job("parse_cvs", {"campaign_id": campaign_id})
    return {"ok": True, "candidate_ids": created, "job_id": job_id}


@router.get("/{campaign_id}/candidates", response_model=List[CandidateOut])
def list_candidates(campaign_id: int, session: SessionDep) -> List[CandidateOut]:
    rows = (
        session.query(models.Candidate)
        .filter(models.Candidate.campaign_id == campaign_id)
        .order_by(models.Candidate.id.desc())
        .all()
    )
    return [
        CandidateOut(
            id=r.id,
            filename=r.filename,
            parse_status=r.parse_status,
            error=r.error,
            parse_method=getattr(r, "parse_method", "unknown") or "unknown",
            chars=len((r.text or "").strip()),
            quality_score=float(getattr(r, "quality_score", 0.0) or 0.0),
            quality_reason=str(getattr(r, "quality_reason", "") or ""),
        )
        for r in rows
    ]


@router.post("/{campaign_id}/screen")
def start_screening(campaign_id: int, session: SessionDep) -> dict:
    campaign = session.get(models.Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    job_id = enqueue_job("screen_campaign", {"campaign_id": campaign_id})
    return {"ok": True, "job_id": job_id}


@router.get("/{campaign_id}/ranking")
def get_ranking(campaign_id: int, session: SessionDep) -> dict:
    rows = (
        session.query(models.ScreeningResult)
        .filter(models.ScreeningResult.campaign_id == campaign_id)
        .order_by(models.ScreeningResult.score_embed.desc())
        .all()
    )
    import json
    return {
        "campaign_id": campaign_id,
        "results": [
            {
                "candidate_id": r.candidate_id,
                "score": r.score_embed,
                "notes": r.notes,
                "evidence": json.loads(getattr(r, "evidence_json", "[]") or "[]"),
            }
            for r in rows
        ],
    }


@router.post("/{campaign_id}/candidates/{candidate_id}/review")
def start_review(campaign_id: int, candidate_id: int, session: SessionDep) -> dict:
    campaign = session.get(models.Campaign, campaign_id)
    cand = session.get(models.Candidate, candidate_id)
    if campaign is None or cand is None or cand.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Campaign/Candidate not found")

    job_id = enqueue_job("review_candidate", {"campaign_id": campaign_id, "candidate_id": candidate_id})
    return {"ok": True, "job_id": job_id}


@router.post("/{campaign_id}/candidates/{candidate_id}/profile")
def start_profile_extract(campaign_id: int, candidate_id: int, session: SessionDep) -> dict:
    campaign = session.get(models.Campaign, campaign_id)
    cand = session.get(models.Candidate, candidate_id)
    if campaign is None or cand is None or cand.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Campaign/Candidate not found")
    job_id = enqueue_job("extract_profile", {"campaign_id": campaign_id, "candidate_id": candidate_id})
    return {"ok": True, "job_id": job_id}


@router.get("/{campaign_id}/candidates/{candidate_id}/profile", response_model=CandidateProfileOut)
def get_profile(campaign_id: int, candidate_id: int, session: SessionDep) -> CandidateProfileOut:
    cand = session.get(models.Candidate, candidate_id)
    if cand is None or cand.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Candidate not found")

    row = (
        session.query(models.CandidateProfile)
        .filter(models.CandidateProfile.candidate_id == candidate_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    import json

    return CandidateProfileOut(
        candidate_id=candidate_id,
        name=row.name,
        email=row.email,
        phone=row.phone,
        years_experience=float(row.years_experience or 0.0),
        education=row.education,
        skills=json.loads(row.skills_json or "[]"),
    )


@router.get("/{campaign_id}/candidates/{candidate_id}/review", response_model=ReviewOut)
def get_review(campaign_id: int, candidate_id: int, session: SessionDep) -> ReviewOut:
    row = (
        session.query(models.ReviewResult)
        .filter(models.ReviewResult.campaign_id == campaign_id, models.ReviewResult.candidate_id == candidate_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found")

    import json

    return ReviewOut(
        candidate_id=candidate_id,
        score=row.score_llm,
        summary=row.summary,
        strengths=json.loads(row.strengths_json or "[]"),
        gaps=json.loads(row.gaps_json or "[]"),
        evidence=json.loads(row.evidence_json or "[]"),
    )
