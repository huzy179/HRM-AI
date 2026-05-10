from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _poll_job(job_id: str, *, timeout_s: int = 180) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        r = requests.get(_api(f"/jobs/{job_id}"), timeout=15)
        last = r.json()
        if last.get("status") in {"DONE", "FAILED"}:
            return last
        time.sleep(1.0)
    return last


def main() -> None:
    st.set_page_config(page_title="CV Screening (API)", page_icon="🧾", layout="wide")
    st.title("🧾 CV Screening — Phase 2 (API + Worker)")
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
        st.subheader("2) Upload JD (PDF/TXT)")
        jd = st.file_uploader("JD file", type=["pdf", "txt"], accept_multiple_files=False)
        if st.button("Upload JD") and jd is not None:
            files = {"file": (jd.name, jd.getvalue(), "application/octet-stream")}
            res = requests.post(_api(f"/campaigns/{campaign_id}/jd"), files=files, timeout=120).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")

    st.subheader("3) Upload CVs (PDF)")
    cvs = st.file_uploader("CV PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Upload CVs") and cvs:
        files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in cvs]
        res = requests.post(_api(f"/campaigns/{campaign_id}/cvs"), files=files, timeout=300).json()
        st.json(res)
        st.session_state["last_job_id"] = res.get("job_id")

    st.subheader("4) Jobs")
    job_id = st.text_input("Job ID", value=st.session_state.get("last_job_id", "") or "")
    if st.button("Poll job") and job_id.strip():
        st.json(_poll_job(job_id.strip(), timeout_s=180))

    st.subheader("5) Candidates")
    if st.button("Refresh candidates"):
        st.session_state["candidates"] = requests.get(_api(f"/campaigns/{campaign_id}/candidates"), timeout=30).json()
    candidates = st.session_state.get("candidates") or requests.get(_api(f"/campaigns/{campaign_id}/candidates"), timeout=30).json()
    df_cand = pd.DataFrame(candidates) if candidates else pd.DataFrame(columns=["id", "filename", "parse_status", "error"])
    st.dataframe(df_cand, use_container_width=True)

    st.subheader("6) Screening")
    if st.button("Start screening"):
        res = requests.post(_api(f"/campaigns/{campaign_id}/screen"), timeout=60).json()
        st.json(res)
        st.session_state["last_job_id"] = res.get("job_id")

    if st.button("Get ranking"):
        ranking = requests.get(_api(f"/campaigns/{campaign_id}/ranking"), timeout=60).json()
        rows = ranking.get("results") or []
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("score", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.session_state["ranking"] = rows

    ranking_rows = st.session_state.get("ranking") or []
    if ranking_rows:
        st.subheader("7) Review (llama3)")
        candidate_ids = [r["candidate_id"] for r in ranking_rows]
        selected_id = st.selectbox("Candidate", options=candidate_ids)
        if st.button("Start review"):
            res = requests.post(_api(f"/campaigns/{campaign_id}/candidates/{selected_id}/review"), timeout=60).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")

        if st.button("Get review"):
            r = requests.get(_api(f"/campaigns/{campaign_id}/candidates/{selected_id}/review"), timeout=60)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.json(r.json())


if __name__ == "__main__":
    main()

