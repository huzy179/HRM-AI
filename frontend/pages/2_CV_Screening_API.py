from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _poll_job(job_id: str, *, timeout_s: int = 180) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        r = requests.get(_api(f"/jobs/{job_id}"), timeout=15)
        last = r.json()
        if last.get("status") in {"DONE", "FAILED"}:
            return last
        time.sleep(1.0)
    return last


def _safe_get_json(resp: requests.Response) -> Tuple[bool, Any]:
    try:
        return True, resp.json()
    except Exception:
        return False, resp.text


def _badge(text: str, *, ok: bool) -> str:
    return f"✅ {text}" if ok else f"❌ {text}"


def main() -> None:
    st.set_page_config(page_title="CV Screening (API)", page_icon="🧾", layout="wide")
    st.title("🧾 CV Screening — API + Worker")
    st.caption(f"API: `{API_BASE_URL}`")

    if "campaign_id" not in st.session_state:
        st.session_state["campaign_id"] = None

    col_a, col_b = st.columns([1, 1], gap="large")
    with col_a:
        st.subheader("1) Campaign")
        if st.button("Refresh campaigns"):
            st.session_state["campaigns"] = requests.get(_api("/campaigns"), timeout=30).json()

        campaigns = st.session_state.get("campaigns") or requests.get(_api("/campaigns"), timeout=30).json()
        options = [None, *campaigns]
        selected = st.selectbox(
            "Chọn campaign",
            options=options,
            format_func=lambda x: "(Tạo mới)" if x is None else f"{x['id']}: {x['name']}",
        )

        if selected is None:
            new_name = st.text_input("Campaign name", value="Campaign 1")
            if st.button("Create"):
                created = requests.post(_api("/campaigns"), json={"name": new_name}, timeout=30).json()
                st.success(f"Created campaign {created['id']}")
                st.session_state["campaign_id"] = created["id"]
        else:
            st.session_state["campaign_id"] = selected["id"]

    campaign_id = st.session_state.get("campaign_id")
    if not campaign_id:
        st.info("Tạo hoặc chọn 1 campaign để tiếp tục.")
        return

    with col_b:
        st.subheader("2) Upload JD")
        jd = st.file_uploader(
            "JD file (PDF/TXT/PNG/JPG)",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        if st.button("Upload JD") and jd is not None:
            files = {"file": (jd.name, jd.getvalue(), "application/octet-stream")}
            res = requests.post(_api(f"/campaigns/{campaign_id}/jd"), files=files, timeout=120).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")

    st.subheader("3) Upload CVs")
    cvs = st.file_uploader(
        "CV files (PDF/PNG/JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if st.button("Upload CVs") and cvs:
        files = [("files", (f.name, f.getvalue(), "application/octet-stream")) for f in cvs]
        res = requests.post(_api(f"/campaigns/{campaign_id}/cvs"), files=files, timeout=300).json()
        st.json(res)
        st.session_state["last_job_id"] = res.get("job_id")

    st.subheader("4) Jobs")
    job_id = st.text_input("Job ID", value=st.session_state.get("last_job_id", "") or "")
    if st.button("Poll job") and job_id.strip():
        data = _poll_job(job_id.strip(), timeout_s=180)
        st.json(data)
        if isinstance(data, dict) and data.get("duration_ms") is not None:
            st.caption(
                f"duration_ms: {data.get('duration_ms')} | started_at: {data.get('started_at')} | finished_at: {data.get('finished_at')}"
            )

    st.subheader("5) Candidates")
    if st.button("Refresh candidates"):
        st.session_state["candidates"] = requests.get(_api(f"/campaigns/{campaign_id}/candidates"), timeout=30).json()
    candidates = st.session_state.get("candidates") or requests.get(_api(f"/campaigns/{campaign_id}/candidates"), timeout=30).json()

    df_cand = pd.DataFrame(candidates) if candidates else pd.DataFrame(columns=["id", "filename", "parse_status", "error"])
    if not df_cand.empty:
        cols = [
            c
            for c in [
                "id",
                "filename",
                "parse_status",
                "parse_method",
                "chars",
                "quality_score",
                "quality_reason",
                "error",
            ]
            if c in df_cand.columns
        ]
        df_cand = df_cand[cols]

    with st.expander("Candidates table", expanded=False):
        st.dataframe(df_cand, use_container_width=True, height=260)

    st.subheader("6) Screening")
    col_s1, col_s2 = st.columns([1, 1], gap="large")
    with col_s1:
        if st.button("Start screening"):
            res = requests.post(_api(f"/campaigns/{campaign_id}/screen"), timeout=60).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")
    with col_s2:
        if st.button("Get ranking"):
            ranking = requests.get(_api(f"/campaigns/{campaign_id}/ranking"), timeout=60).json()
            rows = ranking.get("results") or []
            st.session_state["ranking"] = rows
            st.session_state["ranking_df"] = pd.DataFrame(rows)

    ranking_rows: List[Dict[str, Any]] = st.session_state.get("ranking") or []
    ranking_df = st.session_state.get("ranking_df")

    st.subheader("6.1) Ranking dashboard")
    if ranking_df is None or (isinstance(ranking_df, pd.DataFrame) and ranking_df.empty):
        st.info("Nhấn `Get ranking` để xem kết quả.")
        return

    df_rank = ranking_df.copy()
    sort_col = "score_total" if "score_total" in df_rank.columns else ("score" if "score" in df_rank.columns else None)
    if sort_col:
        df_rank = df_rank.sort_values(sort_col, ascending=False)

    cand_map: Dict[int, Dict[str, Any]] = {}
    for c in candidates or []:
        try:
            cand_map[int(c.get("id"))] = c
        except Exception:
            continue

    df_rank["filename"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("filename", ""))
    df_rank["parse_status"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("parse_status", ""))
    df_rank["parse_method"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("parse_method", ""))
    df_rank["quality_score"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("quality_score", 0.0))
    df_rank["quality_reason"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("quality_reason", ""))
    df_rank["error"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("error", ""))

    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1], gap="large")
    with col_f1:
        only_ok = st.checkbox("Chỉ OK", value=True)
    with col_f2:
        min_total = st.slider("Min score_total", min_value=0, max_value=100, value=0)
    with col_f3:
        min_embed = st.slider("Min score_embed", min_value=0, max_value=100, value=0)
    with col_f4:
        show_errors = st.checkbox("Hiển thị lỗi/quality", value=True)

    if only_ok:
        df_rank = df_rank[df_rank["parse_status"] == "OK"]
    if "score_total" in df_rank.columns:
        df_rank = df_rank[df_rank["score_total"].fillna(0) >= min_total]
    if "score_embed" in df_rank.columns:
        df_rank = df_rank[df_rank["score_embed"].fillna(0) >= min_embed]

    show_cols = [
        c
        for c in [
            "candidate_id",
            "filename",
            "score_total",
            "score_embed",
            "score_rules",
            "parse_status",
            "parse_method",
            "quality_score",
            "quality_reason",
            "error",
            "notes",
        ]
        if c in df_rank.columns
    ]
    df_view = df_rank[show_cols].copy()
    if not show_errors:
        for c in ["quality_score", "quality_reason", "error"]:
            if c in df_view.columns:
                df_view = df_view.drop(columns=[c])

    def _style(row: pd.Series):
        parse_status = str(row.get("parse_status") or "")
        q_reason = str(row.get("quality_reason") or "")
        if parse_status != "OK":
            return ["background-color: #3a1a1a"] * len(row)
        if q_reason:
            return ["background-color: #3a2a12"] * len(row)
        return [""] * len(row)

    try:
        st.dataframe(df_view.style.apply(_style, axis=1), use_container_width=True, height=320)
    except Exception:
        st.dataframe(df_view, use_container_width=True, height=320)

    st.subheader("6.2) Candidate drill-down")
    visible_candidate_ids = df_view["candidate_id"].tolist() if not df_view.empty else []
    if not visible_candidate_ids:
        st.warning("Không có candidate nào match filter.")
        return

    selected_id = st.selectbox("Candidate", options=visible_candidate_ids, key="drill_candidate_id")
    row = next((x for x in ranking_rows if int(x.get("candidate_id")) == int(selected_id)), None) or {}
    cand_meta = cand_map.get(int(selected_id)) or {}

    col_d1, col_d2, col_d3, col_d4 = st.columns([1, 1, 1, 1], gap="large")
    with col_d1:
        st.metric("score_total", float(row.get("score_total") or 0.0))
    with col_d2:
        st.metric("score_embed", float(row.get("score_embed") or 0.0))
    with col_d3:
        st.metric("score_rules", float(row.get("score_rules") or 0.0))
    with col_d4:
        st.metric("quality_score", float(cand_meta.get("quality_score") or 0.0))

    st.caption(
        f"{_badge('parse_status=' + str(cand_meta.get('parse_status')), ok=str(cand_meta.get('parse_status'))=='OK')} | "
        f"method={cand_meta.get('parse_method')} | file={cand_meta.get('filename')}"
    )
    if cand_meta.get("error"):
        st.error(f"Candidate error: {cand_meta.get('error')}")
    if cand_meta.get("quality_reason"):
        st.warning(f"OCR quality: {cand_meta.get('quality_reason')}")

    tabs = st.tabs(["Evidence", "Rules", "Review", "Profile"])

    with tabs[0]:
        ev = row.get("evidence") or []
        if not ev:
            st.info("Không có evidence.")
        else:
            for i, chunk in enumerate(ev, start=1):
                st.text_area(f"Chunk {i}", value=str(chunk)[:9000], height=200)

    with tabs[1]:
        rules = row.get("rules")
        if rules is None:
            st.info("Không có rules.")
        else:
            st.json(rules)

    with tabs[2]:
        col_r1, col_r2 = st.columns([1, 1], gap="large")
        with col_r1:
            if st.button("Start review", key="btn_start_review"):
                res = requests.post(_api(f"/campaigns/{campaign_id}/candidates/{selected_id}/review"), timeout=60)
                ok, payload = _safe_get_json(res)
                if ok:
                    st.json(payload)
                    st.session_state["last_job_id"] = (payload or {}).get("job_id")
                else:
                    st.error(payload)
        with col_r2:
            if st.button("Get review", key="btn_get_review"):
                r = requests.get(_api(f"/campaigns/{campaign_id}/candidates/{selected_id}/review"), timeout=60)
                if r.status_code != 200:
                    st.error(r.text)
                else:
                    st.json(r.json())

    with tabs[3]:
        col_p1, col_p2 = st.columns([1, 1], gap="large")
        with col_p1:
            if st.button("Start profile extract", key="btn_start_profile"):
                res = requests.post(
                    _api(f"/campaigns/{campaign_id}/candidates/{selected_id}/profile"),
                    timeout=60,
                )
                ok, payload = _safe_get_json(res)
                if ok:
                    st.json(payload)
                    st.session_state["last_job_id"] = (payload or {}).get("job_id")
                else:
                    st.error(payload)
        with col_p2:
            if st.button("Get profile", key="btn_get_profile"):
                r = requests.get(
                    _api(f"/campaigns/{campaign_id}/candidates/{selected_id}/profile"),
                    timeout=30,
                )
                if r.status_code != 200:
                    st.error(r.text)
                else:
                    st.json(r.json())


if __name__ == "__main__":
    main()

