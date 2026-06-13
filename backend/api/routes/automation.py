from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import SessionDep
from backend.db import models
from backend.core.config import get_settings
from langchain_ollama import ChatOllama
from backend.services.ollama_utils import invoke_with_retry
from backend.core.tenant import current_tenant_id

router = APIRouter()


class EmailGenerationIn(BaseModel):
    campaign_id: int
    candidate_id: int
    email_type: str  # "interview", "rejection", "offer"


class EmailGenerationOut(BaseModel):
    email_content: str
    email_subject: str


@router.post("/generate-email", response_model=EmailGenerationOut)
def generate_email(payload: EmailGenerationIn, session: SessionDep) -> EmailGenerationOut:
    tenant_id = current_tenant_id()
    
    # 1. Fetch Campaign and Candidate
    camp = session.query(models.Campaign).filter(models.Campaign.id == payload.campaign_id, models.Campaign.tenant_id == tenant_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    cand = session.query(models.Candidate).filter(models.Candidate.id == payload.candidate_id, models.Candidate.tenant_id == tenant_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    profile = session.query(models.CandidateProfile).filter(models.CandidateProfile.candidate_id == cand.id).first()
    candidate_name = profile.name if profile and profile.name else cand.filename

    # 2. Fetch Review Result
    review = session.query(models.ReviewResult).filter(
        models.ReviewResult.campaign_id == payload.campaign_id,
        models.ReviewResult.candidate_id == payload.candidate_id,
        models.ReviewResult.tenant_id == tenant_id
    ).first()

    score = review.score_llm if review else 0
    strengths = ""
    gaps = ""
    if review:
        try:
            st_list = json.loads(review.strengths_json)
            strengths = ", ".join(st_list)
        except Exception:
            strengths = review.strengths_json
        try:
            gap_list = json.loads(review.gaps_json)
            gaps = ", ".join(gap_list)
        except Exception:
            gaps = review.gaps_json

    # 3. Determine email parameters
    t = payload.email_type.lower().strip()
    if t == "interview":
        type_str = "Mời phỏng vấn trực tiếp"
        subject = f"[HRM AI] Thư mời phỏng vấn - Vị trí {camp.name}"
    elif t == "rejection":
        type_str = "Từ chối hồ sơ ứng viên khéo léo và lịch sự"
        subject = f"[HRM AI] Phản hồi kết quả ứng tuyển - Vị trí {camp.name}"
    elif t == "offer":
        type_str = "Thư mời nhận việc (Job Offer)"
        subject = f"[HRM AI] Thư mời nhận việc - Vị trí {camp.name}"
    else:
        raise HTTPException(status_code=400, detail="Invalid email_type. Supported values: interview, rejection, offer")

    # 4. Invoke LLM to generate email content
    s = get_settings()
    llm = ChatOllama(
        model=s.ollama_chat_model,
        base_url=s.ollama_base_url,
        temperature=0.7,  # slightly higher temperature for email natural phrasing
        client_kwargs={"timeout": s.ollama_timeout_s},
    )

    prompt = (
        "Bạn là Trưởng bộ phận Tuyển dụng (HR Manager) viết email gửi tới ứng viên.\n"
        "Hãy viết một email phản hồi chi tiết gửi tới ứng viên dựa trên thông tin tuyển dụng sau:\n"
        f"Tên ứng viên: {candidate_name}\n"
        f"Vị trí ứng tuyển: {camp.name}\n"
        f"Mục đích email: {type_str}\n"
        "Kết quả đánh giá hồ sơ ứng viên:\n"
        f"- Điểm số phù hợp: {score}/100\n"
        f"- Các thế mạnh nổi bật: {strengths if strengths else 'Không ghi nhận'}\n"
        f"- Các điểm chưa phù hợp: {gaps if gaps else 'Không ghi nhận'}\n\n"
        "Yêu cầu nội dung email:\n"
        "1. Email viết hoàn toàn bằng tiếng Việt với văn phong lịch sự, trang trọng nhưng vẫn thân thiện.\n"
        "2. Cá nhân hóa email. Nếu là thư phỏng vấn/nhận việc, hãy khen ngợi các điểm mạnh nổi bật. Nếu là thư từ chối, hãy cảm ơn chân thành, chỉ ra nhẹ nhàng các điểm chưa phù hợp và động viên cơ hội hợp tác sau này.\n"
        "3. Trả về đúng nội dung email hoàn chỉnh bắt đầu từ 'Kính gửi...' đến hết phần chữ ký của phòng Tuyển dụng, không chứa thêm bất kỳ bình luận hay ghi chú giải thích nào khác."
    )

    try:
        response = invoke_with_retry(
            llm,
            prompt,
            retries=s.ollama_retries,
            backoff_s=s.ollama_retry_backoff_s,
        )
        content = (getattr(response, "content", "") or "").strip()
    except Exception as e:
        content = (
            f"Kính gửi {candidate_name},\n\n"
            f"Cảm ơn bạn đã quan tâm đến vị trí {camp.name}. Hệ thống AI đang gặp sự cố kết nối LLM tạm thời.\n"
            f"Vui lòng thử lại sau.\n\n"
            f"Trân trọng,\nPhòng Tuyển dụng HRM AI"
        )

    return EmailGenerationOut(
        email_content=content,
        email_subject=subject
    )


class CandidateStatusIn(BaseModel):
    pipeline_status: str


@router.put("/candidates/{candidate_id}/status")
def update_candidate_status(candidate_id: int, payload: CandidateStatusIn, session: SessionDep) -> dict:
    tenant_id = current_tenant_id()
    cand = session.query(models.Candidate).filter(models.Candidate.id == candidate_id, models.Candidate.tenant_id == tenant_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    cand.pipeline_status = payload.pipeline_status.strip()
    session.commit()
    return {"ok": True, "pipeline_status": cand.pipeline_status}
