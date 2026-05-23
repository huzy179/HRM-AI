from __future__ import annotations

import os
from typing import List, Optional

import requests
import streamlit as st

from frontend import api_client


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def main() -> None:
    st.set_page_config(page_title="Phase 2 API", page_icon="🧩", layout="wide")
    st.title("🧩 Phase 2 — API Demo")
    st.caption(f"API: `{API_BASE_URL}`")

    st.subheader("1) Create campaign")
    name = st.text_input("Campaign name", value="Campaign 1")
    if st.button("Create campaign"):
        r = api_client.post("/campaigns", json={"name": name}, timeout=30)
        st.write(r.status_code)
        st.json(r.json())

    st.subheader("2) List campaigns")
    if st.button("Refresh campaigns"):
        r = api_client.get("/campaigns", timeout=30)
        st.json(r.json())

    st.subheader("3) Upload JD (PDF/TXT)")
    campaign_id = st.number_input("Campaign ID", min_value=1, value=1, step=1)
    jd = st.file_uploader("JD file", type=["pdf", "txt"], accept_multiple_files=False, key="jd_file")
    if st.button("Upload JD") and jd is not None:
        files = {"file": (jd.name, jd.getvalue(), "application/octet-stream")}
        r = api_client.post(f"/campaigns/{campaign_id}/jd", files=files, timeout=120)
        st.json(r.json())

    st.subheader("4) Upload CVs (PDF)")
    cvs = st.file_uploader("CV PDFs", type=["pdf"], accept_multiple_files=True, key="cv_files")
    if st.button("Upload CVs") and cvs:
        files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in cvs]
        r = api_client.post(f"/campaigns/{campaign_id}/cvs", files=files, timeout=300)
        st.json(r.json())

    st.subheader("5) Start screening")
    if st.button("Start screening job"):
        r = api_client.post(f"/campaigns/{campaign_id}/screen", timeout=60)
        st.json(r.json())

    st.subheader("6) Check job status")
    job_id = st.text_input("Job ID")
    if st.button("Get job") and job_id.strip():
        r = api_client.get(f"/jobs/{job_id.strip()}", timeout=30)
        data = r.json()
        st.json(data)
        if isinstance(data, dict) and data.get("duration_ms") is not None:
            st.caption(
                f"duration_ms: {data.get('duration_ms')} | started_at: {data.get('started_at')} | finished_at: {data.get('finished_at')}"
            )

    st.subheader("7) Ranking")
    if st.button("Get ranking"):
        r = api_client.get(f"/campaigns/{campaign_id}/ranking", timeout=60)
        st.json(r.json())


if __name__ == "__main__":
    main()
