from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    project_root: Path

    raw_cv_dir: Path
    sample_jd_dir: Path
    policy_docs_dir: Path

    chroma_dir: Path
    chroma_cv_screening_dir: Path
    chroma_collection_cvs: str

    ollama_embed_model: str
    ollama_base_url: str
    ollama_chat_model: str

    cv_chunk_size: int
    cv_chunk_overlap: int


def get_settings(project_root: Path | None = None) -> Settings:
    root = project_root or Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    chroma_dir = data_dir / "chroma_db"

    return Settings(
        project_root=root,
        raw_cv_dir=data_dir / "raw_cv",
        sample_jd_dir=data_dir / "sample_jd",
        policy_docs_dir=data_dir / "policy_docs",
        chroma_dir=chroma_dir,
        chroma_cv_screening_dir=chroma_dir / "cv_screening",
        chroma_collection_cvs="cvs",
        ollama_embed_model="nomic-embed-text",
        ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_chat_model=os.environ.get("OLLAMA_CHAT_MODEL", "llama3"),
        cv_chunk_size=int(os.environ.get("CV_CHUNK_SIZE", "1000")),
        cv_chunk_overlap=int(os.environ.get("CV_CHUNK_OVERLAP", "150")),
    )


def ensure_dirs(settings: Settings | None = None) -> None:
    s = settings or get_settings()
    s.raw_cv_dir.mkdir(parents=True, exist_ok=True)
    s.sample_jd_dir.mkdir(parents=True, exist_ok=True)
    s.policy_docs_dir.mkdir(parents=True, exist_ok=True)
    s.chroma_cv_screening_dir.mkdir(parents=True, exist_ok=True)
