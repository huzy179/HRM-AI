from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(\+?84|0)\s*(\d[\d\s().-]{7,}\d)")


@dataclass(frozen=True)
class CandidateProfileExtracted:
    name: str = ""
    email: str = ""
    phone: str = ""
    years_experience: float = 0.0
    education: str = ""
    skills: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.skills is None:
            object.__setattr__(self, "skills", [])


_SKILL_KEYWORDS = [
    "python",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgres",
    "mysql",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "langchain",
    "rag",
    "llm",
    "pandas",
    "numpy",
    "opencv",
]


def _first_non_empty_line(text: str) -> str:
    for line in (text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _extract_years(text: str) -> float:
    t = (text or "").lower()
    candidates: list[float] = []

    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", t):
        try:
            candidates.append(float(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*năm\b", t):
        try:
            candidates.append(float(m.group(1)))
        except Exception:
            pass

    if not candidates:
        return 0.0
    # choose a conservative max but cap at 50
    return float(max(0.0, min(50.0, max(candidates))))


def extract_candidate_profile(text: str) -> CandidateProfileExtracted:
    t = text or ""

    # Try LLM extraction first
    try:
        from langchain_ollama import ChatOllama
        from backend.core.config import get_settings
        from backend.services.ollama_utils import invoke_with_retry
        import json

        s = get_settings()
        llm = ChatOllama(
            model=s.ollama_chat_model,
            base_url=s.ollama_base_url,
            temperature=0,
            format="json",
            client_kwargs={"timeout": s.ollama_timeout_s},
        )

        prompt = (
            "Bạn là trợ lý AI chuyên trích xuất thông tin hồ sơ từ CV tuyển dụng.\n"
            "Hãy phân tích văn bản CV dưới đây và trích xuất các thông tin chính xác nhất.\n"
            "Định dạng trả về PHẢI là một đối tượng JSON hợp lệ duy nhất, không có markdown hoặc text ngoài, theo cấu trúc:\n"
            "{\n"
            '  "name": "Họ tên đầy đủ của ứng viên (nếu tìm thấy, nếu không để trống)",\n'
            '  "email": "Địa chỉ email (nếu tìm thấy, nếu không để trống)",\n'
            '  "phone": "Số điện thoại liên hệ (nếu tìm thấy, nếu không để trống)",\n'
            '  "years_experience": số năm kinh nghiệm làm việc thực tế (trả về kiểu số thực, ví dụ: 2.5 hoặc 5.0, mặc định là 0.0 nếu chưa có kinh nghiệm hoặc không tìm thấy)",\n'
            '  "education": "Tên trường đại học và chuyên ngành hoặc bằng cấp cao nhất (nếu tìm thấy, nếu không để trống)",\n'
            '  "skills": ["danh sách các kỹ năng chuyên môn, lập trình, công nghệ của ứng viên, dạng mảng các chuỗi"]\n'
            "}\n\n"
            "VĂN BẢN CV:\n"
            f"{t}\n"
        )

        response = invoke_with_retry(
            llm,
            prompt,
            retries=s.ollama_retries,
            backoff_s=s.ollama_retry_backoff_s,
        )
        content = (getattr(response, "content", "") or "").strip()
        data = json.loads(content)

        # Parse extracted values
        name = str(data.get("name") or "").strip()
        email = str(data.get("email") or "").strip()
        phone = str(data.get("phone") or "").strip()
        
        try:
            years = float(data.get("years_experience") or 0.0)
        except Exception:
            years = 0.0
            
        education = str(data.get("education") or "").strip()
        skills = [str(x).strip().lower() for x in (data.get("skills") or []) if str(x).strip()]
        
        # Fallback fields if LLM leaves crucial items empty but they exist in text
        if not email:
            m = _EMAIL_RE.search(t)
            if m:
                email = m.group(0).strip()
        if not phone:
            m2 = _PHONE_RE.search(t)
            if m2:
                phone = (m2.group(0) or "").strip()

        # Cap experience
        years = float(max(0.0, min(50.0, years)))

        if name or email or phone or skills or education:
            return CandidateProfileExtracted(
                name=name,
                email=email,
                phone=phone,
                years_experience=years,
                education=education,
                skills=sorted(list(set(skills))),
            )
    except Exception:
        # Fallback gracefully
        pass

    # Existing rule-based fallback
    email = ""
    m = _EMAIL_RE.search(t)
    if m:
        email = m.group(0).strip()

    phone = ""
    m2 = _PHONE_RE.search(t)
    if m2:
        phone = (m2.group(0) or "").strip()

    name = _first_non_empty_line(t)
    if len(name) > 80 or ("@" in name) or any(k in name.lower() for k in ["curriculum", "resume", "cv"]):
        name = ""

    years = _extract_years(t)

    lower = t.lower()
    skills = []
    for kw in _SKILL_KEYWORDS:
        if kw in lower:
            skills.append(kw)
    skills = sorted(set(skills))

    education = ""
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(x in s.lower() for x in ["university", "college", "đại học", "cao đẳng", "bachelor", "master"]):
            education = s[:400]
            break

    return CandidateProfileExtracted(
        name=name,
        email=email,
        phone=phone,
        years_experience=years,
        education=education,
        skills=skills,
    )

