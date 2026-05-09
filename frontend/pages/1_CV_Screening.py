from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import get_settings  # noqa: E402
from backend.services.cv_parser import parse_cv  # noqa: E402
from backend.services.matcher import CVMatcher  # noqa: E402
from backend.services.llm_scorer import review_with_llama3  # noqa: E402


@st.cache_resource
def get_matcher() -> CVMatcher:
    return CVMatcher()


def _load_jd_sample_files() -> List[Path]:
    settings = get_settings()
    if not settings.sample_jd_dir.exists():
        return []
    return sorted([p for p in settings.sample_jd_dir.glob("*.txt") if p.is_file()])


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _save_upload_to_temp(upload) -> Path:
    suffix = Path(upload.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload.getbuffer())
        return Path(tmp.name)


def _list_local_pdfs() -> List[Path]:
    settings = get_settings()
    if not settings.raw_cv_dir.exists():
        return []
    return sorted([p for p in settings.raw_cv_dir.glob("*.pdf") if p.is_file()])


def main() -> None:
    st.set_page_config(page_title="CV Screening", page_icon="🧾", layout="wide")
    st.title("🧾 CV Screening (Phase 1)")

    matcher = get_matcher()
    st.session_state.setdefault("screening", {})

    with st.sidebar:
        st.header("⚙️ Settings")
        st.write(f"`OLLAMA_BASE_URL`: `{matcher.settings.ollama_base_url}`")
        st.write(f"`Embed model`: `{matcher.settings.ollama_embed_model}`")
        st.write(f"`Chroma dir`: `{matcher.settings.chroma_cv_screening_dir}`")
        st.write(f"`Chunk`: `{matcher.settings.cv_chunk_size}` / overlap `{matcher.settings.cv_chunk_overlap}`")

        reset = st.button("Reset Chroma collection", type="secondary")
        if reset:
            matcher.reset_collection()
            st.session_state["screening"] = {}
            st.success("Collection reset.")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("1) Job Description")

        jd_files = _load_jd_sample_files()
        jd_sample: Optional[Path] = None
        if jd_files:
            jd_sample = st.selectbox(
                "Chọn JD mẫu (txt) (optional)",
                options=[None, *jd_files],
                format_func=lambda p: "(Không dùng JD mẫu)" if p is None else p.name,
            )

        st.caption("Bạn có thể upload JD dạng PDF/TXT hoặc nhập/paste trực tiếp.")
        jd_upload = st.file_uploader("Upload JD (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=False)

        default_jd = _read_text_file(jd_sample) if jd_sample else ""
        if jd_upload is not None:
            uploaded_suffix = Path(jd_upload.name).suffix.lower()
            if uploaded_suffix == ".pdf":
                tmp_path = _save_upload_to_temp(jd_upload)
                parsed = parse_cv(tmp_path)
                if parsed.error:
                    st.error(f"Không đọc được JD PDF: {parsed.error}")
                else:
                    default_jd = parsed.raw_text
            else:
                default_jd = jd_upload.getvalue().decode("utf-8", errors="ignore")

        jd_text = st.text_area("JD text", value=default_jd, height=280, placeholder="Paste Job Description ở đây...")

    with col_right:
        st.subheader("2) CV PDFs")
        uploads = st.file_uploader(
            "Upload nhiều CV (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
        )
        use_local = st.checkbox("Dùng luôn PDF trong `data/raw_cv/`", value=False)
        local_pdfs = _list_local_pdfs() if use_local else []
        if use_local:
            st.caption(f"Tìm thấy {len(local_pdfs)} PDF trong `data/raw_cv/`.")

        st.info("Nếu CV là PDF scan (ảnh), cần OCR. Docker image đã có Tesseract; chạy local thì phải cài Tesseract.")

    run = st.button("🚀 Run screening", type="primary")

    jd_text = (jd_text or "").strip()
    screening = st.session_state["screening"]

    if run:
        if not jd_text:
            st.error("Bạn cần nhập Job Description.")
            return
        if not uploads and not local_pdfs:
            st.error("Bạn cần upload ít nhất 1 CV PDF hoặc bật dùng `data/raw_cv/`.")
            return

        matcher.reset_collection()

        cv_rows: List[dict] = []
        parse_results = []

        st.subheader("3) Parse & Index")
        progress = st.progress(0, text="Starting...")
        total = len(uploads) + len(local_pdfs)
        done = 0

        # Uploads
        for up in uploads or []:
            tmp_path = _save_upload_to_temp(up)
            result = parse_cv(tmp_path)
            parse_results.append(result)
            cv_rows.append(
                {
                    "cv_id": result.cv_id,
                    "chars": len(result.raw_text),
                    "error": result.error,
                }
            )
            done += 1
            progress.progress(int(done / total * 100), text=f"Parsed {done}/{total}: {result.cv_id}")

        # Local PDFs
        for pdf_path in local_pdfs:
            result = parse_cv(pdf_path)
            parse_results.append(result)
            cv_rows.append(
                {
                    "cv_id": result.cv_id,
                    "chars": len(result.raw_text),
                    "error": result.error,
                }
            )
            done += 1
            progress.progress(int(done / total * 100), text=f"Parsed {done}/{total}: {result.cv_id}")

        progress.progress(100, text="Indexing...")
        matcher.index_cvs(parse_results)
        df_parse = pd.DataFrame(cv_rows).sort_values(["error", "chars"], ascending=[True, False])
        st.dataframe(df_parse, use_container_width=True)

        st.subheader("4) Rank")
        ranked = matcher.rank(jd_text=jd_text, k=50)

        ranked_by_id = {r.cv_id: r for r in ranked}
        rows = []
        for cv in parse_results:
            r = ranked_by_id.get(cv.cv_id)
            if r:
                rows.append({"cv_id": r.cv_id, "score": r.score, "status": r.status, "notes": r.notes})
            else:
                rows.append({"cv_id": cv.cv_id, "score": 0.0, "status": "ERROR", "notes": cv.error or "NOT_RANKED"})

        df_rank = pd.DataFrame(rows).sort_values(["score", "cv_id"], ascending=[False, True])
        st.dataframe(df_rank, use_container_width=True)

        screening.clear()
        screening.update(
            {
                "jd_text": jd_text,
                "parse_results": parse_results,
                "df_rank": df_rank,
                "df_parse": df_parse,
                "reviews": {},
            }
        )

    df_rank = screening.get("df_rank")
    if df_rank is None:
        return

    # Render persisted results so buttons work across reruns
    st.subheader("4) Rank")
    st.dataframe(df_rank, use_container_width=True)

    parse_results = screening["parse_results"]
    jd_text = screening["jd_text"]
    df = df_rank

    st.subheader("5) CV details")
    selected = st.selectbox("Chọn CV", options=df["cv_id"].tolist(), key="selected_cv_id")
    selected_parse = next((p for p in parse_results if p.cv_id == selected), None)
    if selected_parse is None:
        return

    st.write(f"Error: `{selected_parse.error}`" if selected_parse.error else "Error: `None`")
    st.text_area("Raw text (preview)", value=(selected_parse.raw_text or "")[:12000], height=320)

    st.subheader("6) LLM review (llama3)")
    st.caption("LLM review dùng top chunks từ Chroma (không đọc toàn bộ CV để giảm token).")

    if st.button("🧠 Generate review (llama3)", type="secondary"):
        with st.spinner("Running llama3..."):
            evidence = matcher.evidence_chunks(jd_text=jd_text, cv_id=selected, k=80, top_n=3)
            review = review_with_llama3(cv_id=selected, jd_text=jd_text, evidence_chunks=evidence)
        screening["reviews"][selected] = review

    review = screening.get("reviews", {}).get(selected)
    if review is not None:
        st.metric("LLM score", review.score)
        st.write("**Summary**")
        st.write(review.summary or "(empty)")
        st.write("**Strengths**")
        st.write(review.strengths or ["(none)"])
        st.write("**Gaps**")
        st.write(review.gaps or ["(none)"])
        with st.expander("Evidence chunks"):
            for i, chunk in enumerate(review.evidence, start=1):
                st.text_area(f"Chunk {i}", value=chunk[:6000], height=180)


if __name__ == "__main__":
    main()
