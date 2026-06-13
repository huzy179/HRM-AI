from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st

from frontend import api_client
from frontend.ui_utils import apply_premium_style, render_auth_gate


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _poll_job(job_id: str, *, timeout_s: int = 180) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        r = api_client.get(f"/jobs/{job_id}", timeout=15)
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
    apply_premium_style()
    # if not render_auth_gate():
    #     return
    st.title("🧾 CV Screening — API + Worker")
    st.caption(f"API: `{API_BASE_URL}`")

    if "campaign_id" not in st.session_state:
        st.session_state["campaign_id"] = None

    col_a, col_b = st.columns([1, 1], gap="large")
    with col_a:
        st.subheader("1) Campaign")
        if st.button("Refresh campaigns"):
            st.session_state["campaigns"] = api_client.get("/campaigns", timeout=30).json()

        campaigns = st.session_state.get("campaigns") or api_client.get("/campaigns", timeout=30).json()
        options = [None, *campaigns]
        selected = st.selectbox(
            "Chọn campaign",
            options=options,
            format_func=lambda x: "(Tạo mới)" if x is None else f"{x['id']}: {x['name']}",
        )

        if selected is None:
            new_name = st.text_input("Campaign name", value="Campaign 1")
            if st.button("Create"):
                created = api_client.post("/campaigns", json={"name": new_name}, timeout=30).json()
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
            "JD file (PDF/TXT/DOCX/MD/PNG/JPG)",
            type=["pdf", "txt", "docx", "md", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        if st.button("Upload JD") and jd is not None:
            files = {"file": (jd.name, jd.getvalue(), "application/octet-stream")}
            res = api_client.post(f"/campaigns/{campaign_id}/jd", files=files, timeout=120).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")

    st.subheader("3) Upload CVs")
    cvs = st.file_uploader(
        "CV files (PDF/DOCX/MD/PNG/JPG)",
        type=["pdf", "docx", "md", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if st.button("Upload CVs") and cvs:
        files = [("files", (f.name, f.getvalue(), "application/octet-stream")) for f in cvs]
        res = api_client.post(f"/campaigns/{campaign_id}/cvs", files=files, timeout=300).json()
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
        st.session_state["candidates"] = api_client.get(f"/campaigns/{campaign_id}/candidates", timeout=30).json()
    candidates = st.session_state.get("candidates") or api_client.get(f"/campaigns/{campaign_id}/candidates", timeout=30).json()

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
    st.subheader("6.0) Campaign settings (composite scoring)")
    try:
        settings_resp = api_client.get(f"/campaigns/{campaign_id}/settings", timeout=20)
        _, camp_settings = _safe_get_json(settings_resp)
    except Exception:
        camp_settings = {}

    w_embed_default = float((camp_settings or {}).get("w_embed", 0.7) or 0.7)
    req_skills_default = (camp_settings or {}).get("required_skills") or []
    min_years_default = float((camp_settings or {}).get("min_years_override", 0.0) or 0.0)

    col_set1, col_set2, col_set3 = st.columns([1, 2, 1], gap="large")
    with col_set1:
        w_embed = st.slider("w_embed (0..1)", min_value=0.0, max_value=1.0, value=float(w_embed_default), step=0.05)
    with col_set2:
        skills_str = st.text_input(
            "Override required skills (comma-separated, optional)",
            value=", ".join([str(x) for x in req_skills_default]),
        )
    with col_set3:
        min_years_override = st.number_input("Min years override", min_value=0.0, max_value=50.0, value=float(min_years_default), step=0.5)

    col_btn1, col_btn2 = st.columns([1, 1], gap="large")
    with col_btn1:
        if st.button("Save settings"):
            skills = [s.strip().lower() for s in (skills_str or "").split(",") if s.strip()]
            payload = {"w_embed": w_embed, "required_skills": skills, "min_years_override": float(min_years_override)}
            r = api_client.put(f"/campaigns/{campaign_id}/settings", json=payload, timeout=30)
            ok, data = _safe_get_json(r)
            if ok and r.status_code < 300:
                st.success("Saved.")
                st.json(data)
            else:
                st.error(data)
    with col_btn2:
        if st.button("Preview JD requirements"):
            r = api_client.get(f"/campaigns/{campaign_id}/requirements", timeout=30)
            ok, data = _safe_get_json(r)
            if ok and r.status_code < 300:
                st.json(data)
            else:
                st.error(data)

    col_s1, col_s2 = st.columns([1, 1], gap="large")
    with col_s1:
        if st.button("Start screening"):
            res = api_client.post(f"/campaigns/{campaign_id}/screen", timeout=60).json()
            st.json(res)
            st.session_state["last_job_id"] = res.get("job_id")
    with col_s2:
        if st.button("Get ranking"):
            ranking = api_client.get(f"/campaigns/{campaign_id}/ranking", timeout=60).json()
            rows = ranking.get("results") or []
            st.session_state["ranking"] = rows
            st.session_state["ranking_df"] = pd.DataFrame(rows)

    ranking_rows: List[Dict[str, Any]] = st.session_state.get("ranking") or []
    ranking_df = st.session_state.get("ranking_df")

    st.subheader("6.1) Ranking dashboard")
    if ranking_df is None or (isinstance(ranking_df, pd.DataFrame) and ranking_df.empty):
        st.info("Nhấn `Get ranking` để xem kết quả.")
        return

    cand_map: Dict[int, Dict[str, Any]] = {}
    for c in candidates or []:
        try:
            cand_map[int(c.get("id"))] = c
        except Exception:
            continue

    # Visualizing top candidates using bar chart
    with st.expander("📊 Score Distribution & Visual Comparison", expanded=True):
        temp_chart_df = ranking_df.copy()
        if not temp_chart_df.empty:
            temp_chart_df["filename"] = temp_chart_df["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("filename", f"Candidate {cid}"))
            chart_data = temp_chart_df.head(10)[["filename", "score_total", "score_embed", "score_rules"]].copy()
            chart_data = chart_data.set_index("filename")
            st.bar_chart(chart_data, y=["score_total", "score_embed", "score_rules"], use_container_width=True)

    df_rank = ranking_df.copy()
    sort_col = "score_total" if "score_total" in df_rank.columns else ("score" if "score" in df_rank.columns else None)
    if sort_col:
        df_rank = df_rank.sort_values(sort_col, ascending=False)

    df_rank["filename"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("filename", ""))
    df_rank["parse_status"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("parse_status", ""))
    df_rank["parse_method"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("parse_method", ""))
    df_rank["quality_score"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("quality_score", 0.0))
    df_rank["quality_reason"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("quality_reason", ""))
    df_rank["error"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("error", ""))
    df_rank["pipeline_status"] = df_rank["candidate_id"].map(lambda cid: (cand_map.get(int(cid)) or {}).get("pipeline_status", "Applied"))

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
            "pipeline_status",
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

    if not df_view.empty:
        csv_data = df_view.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Screening Report (CSV)",
            data=csv_data,
            file_name=f"campaign_{campaign_id}_screening_report.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_download_csv_report"
        )

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

    tabs = st.tabs(["Evidence", "Rules", "Review", "Profile", "📧 Email Automation"])

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
                res = api_client.post(f"/campaigns/{campaign_id}/candidates/{selected_id}/review", timeout=60)
                ok, payload = _safe_get_json(res)
                if ok:
                    st.json(payload)
                    st.session_state["last_job_id"] = (payload or {}).get("job_id")
                else:
                    st.error(payload)
        with col_r2:
            if st.button("Get review", key="btn_get_review"):
                r = api_client.get(f"/campaigns/{campaign_id}/candidates/{selected_id}/review", timeout=60)
                if r.status_code != 200:
                    st.error(r.text)
                else:
                    st.json(r.json())

    with tabs[3]:
        col_p1, col_p2 = st.columns([1, 1], gap="large")
        with col_p1:
            if st.button("Start profile extract", key="btn_start_profile"):
                res = api_client.post(
                    f"/campaigns/{campaign_id}/candidates/{selected_id}/profile",
                    timeout=60,
                )
                ok, payload = _safe_get_json(res)
                if ok:
                    st.json(payload)
                    st.session_state["last_job_id"] = (payload or {}).get("job_id")
                else:
                    st.error(payload)
        with col_p2:
            if st.button("Get profile & View Radar Match", key="btn_get_profile"):
                r_profile = api_client.get(
                    f"/campaigns/{campaign_id}/candidates/{selected_id}/profile",
                    timeout=30,
                )
                r_reqs = api_client.get(
                    f"/campaigns/{campaign_id}/requirements",
                    timeout=30,
                )
                if r_profile.status_code != 200:
                    st.error(r_profile.text)
                else:
                    profile_data = r_profile.json()
                    st.subheader("Candidate Details")
                    st.json(profile_data)
                    
                    # Parse skills and render Radar Chart
                    reqs_data = {}
                    if r_reqs.status_code == 200:
                        try:
                            reqs_data = r_reqs.json()
                        except Exception:
                            pass
                    
                    import json
                    try:
                        cand_skills = json.loads(profile_data.get("skills_json") or "[]")
                        if isinstance(cand_skills, str):
                            cand_skills = json.loads(cand_skills)
                    except Exception:
                        cand_skills = []
                    
                    req_skills = reqs_data.get("required_skills") or []
                    if not req_skills and reqs_data.get("jd_skills"):
                        req_skills = reqs_data.get("jd_skills")
                    
                    if req_skills:
                        import plotly.graph_objects as go
                        
                        cand_skills_lower = {str(s).strip().lower() for s in cand_skills}
                        categories = [str(s).strip() for s in req_skills if str(s).strip()]
                        
                        if categories:
                            fig = go.Figure()
                            # JD Requirements
                            fig.add_trace(go.Scatterpolar(
                                  r=[1] * len(categories),
                                  theta=categories,
                                  fill='toself',
                                  name='JD Requirements',
                                  line_color='rgba(59, 130, 246, 0.6)'
                            ))
                            # Candidate match values
                            cand_values = [1 if c.lower() in cand_skills_lower else 0 for c in categories]
                            fig.add_trace(go.Scatterpolar(
                                  r=cand_values,
                                  theta=categories,
                                  fill='toself',
                                  name='Candidate Skills',
                                  line_color='rgba(239, 68, 68, 0.8)'
                            ))
                            
                            fig.update_layout(
                              polar=dict(
                                radialaxis=dict(
                                  visible=True,
                                  range=[0, 1]
                                )),
                              showlegend=True,
                              title="Radar Chart: Candidate Skills Match vs JD Requirements"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No skill categories found to map on Radar Chart.")
                    else:
                        st.info("No JD required skills defined. Setup requirements in Campaign Settings first.")

    with tabs[4]:
        st.subheader("Pipeline & Email Automation")
        
        # 1. Update Candidate Status
        current_status = cand_meta.get("pipeline_status") or "Applied"
        status_options = ["Applied", "Shortlisted", "Interviewing", "Offered", "Rejected"]
        try:
            status_index = status_options.index(current_status)
        except Exception:
            status_index = 0
            
        new_status = st.selectbox(
            "Change Candidate Pipeline Status",
            options=status_options,
            index=status_index,
            key=f"status_select_{selected_id}"
        )
        if st.button("Update Status", key=f"btn_update_status_{selected_id}"):
            r = api_client.put(f"/automation/candidates/{selected_id}/status", json={"pipeline_status": new_status})
            if r.status_code == 200:
                st.success(f"Updated status to {new_status} successfully!")
                # Refresh candidates list
                st.session_state["candidates"] = api_client.get(f"/campaigns/{campaign_id}/candidates", timeout=30).json()
                st.rerun()
            else:
                st.error(f"Failed to update status: {r.text}")
                
        st.markdown("---")
        
        # 2. Email Generation
        st.subheader("Generate Candidate Response Email")
        email_template = st.selectbox(
            "Select Email Type",
            options=["Interview Invite", "Job Offer", "Rejection Letter"],
            key=f"email_select_{selected_id}"
        )
        
        type_mapping = {
            "Interview Invite": "interview",
            "Job Offer": "offer",
            "Rejection Letter": "rejection"
        }
        
        if st.button("Generate Email Draft", key=f"btn_gen_email_{selected_id}"):
            with st.spinner("Writing personalized email draft..."):
                r = api_client.post(
                    "/automation/generate-email",
                    json={
                        "campaign_id": campaign_id,
                        "candidate_id": selected_id,
                        "email_type": type_mapping[email_template]
                    }
                )
                if r.status_code == 200:
                    data = r.json()
                    st.session_state[f"generated_email_{selected_id}"] = data
                else:
                    st.error(f"Failed to generate email: {r.text}")
                    
        # Display Generated Email if exists
        email_data = st.session_state.get(f"generated_email_{selected_id}")
        if email_data:
            st.markdown("### Generated Email Draft")
            st.text_input("Subject", value=email_data.get("email_subject"), key=f"subject_{selected_id}")
            st.text_area("Content", value=email_data.get("email_content"), height=400, key=f"content_{selected_id}")
            st.caption("You can copy the generated subject and content directly.")


if __name__ == "__main__":
    main()
