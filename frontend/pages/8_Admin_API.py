from __future__ import annotations

import streamlit as st

from frontend import api_client


from frontend.ui_utils import apply_premium_style, render_auth_gate


def main() -> None:
    st.set_page_config(page_title="Admin (API)", page_icon="🛠️", layout="wide")
    apply_premium_style()
    # if not render_auth_gate():
    #     return
    st.title("🛠️ Admin — API")

    st.subheader("1) Audit events")
    col_a1, col_a2, col_a3, col_a4 = st.columns([1, 1, 1, 1], gap="large")
    with col_a1:
        minutes = st.number_input("minutes", min_value=1, max_value=1440, value=60, step=10)
    with col_a2:
        limit = st.number_input("limit", min_value=1, max_value=500, value=200, step=50)
    with col_a3:
        path_prefix = st.text_input("path_prefix", value="")
    with col_a4:
        subject_prefix = st.text_input("subject_prefix", value="")

    if st.button("Load audit events"):
        qp = f"?minutes={int(minutes)}&limit={int(limit)}"
        if path_prefix.strip():
            qp += f"&path_prefix={path_prefix.strip()}"
        if subject_prefix.strip():
            qp += f"&subject_prefix={subject_prefix.strip()}"
        r = api_client.get(f"/audit/events{qp}", timeout=30)
        if r.status_code != 200:
            st.error(r.text)
        else:
            st.dataframe(r.json(), use_container_width=True, height=320)

    st.subheader("2) Purge audit events")
    col_p1, col_p2 = st.columns([1, 1], gap="large")
    with col_p1:
        days = st.number_input("retention days", min_value=1, max_value=3650, value=30, step=1)
    with col_p2:
        confirm = st.checkbox("confirm purge", value=False)

    if st.button("Purge") and confirm:
        r = api_client.post(f"/audit/purge?confirm=true&days={int(days)}", timeout=60)
        if r.status_code != 200:
            if r.status_code == 403:
                st.error("Admin required (set HRM_ADMIN_API_KEY(S) on API and use an admin API_KEY in frontend).")
            else:
                st.error(r.text)
        else:
            st.json(r.json())

    st.subheader("3) Metrics summary")
    col_m1, col_m2 = st.columns([1, 1], gap="large")
    with col_m1:
        m_minutes = st.number_input("metrics minutes", min_value=1, max_value=1440, value=60, step=10)
    with col_m2:
        if st.button("Load metrics"):
            r = api_client.get(f"/metrics/summary?minutes={int(m_minutes)}", timeout=30)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.json(r.json())

    st.subheader("3.1) Jobs (recent) + retry (admin)")
    if st.button("Load jobs"):
        r = api_client.get("/jobs?limit=50", timeout=30)
        if r.status_code != 200:
            st.error(r.text)
        else:
            st.dataframe(r.json(), use_container_width=True, height=260)

    retry_job_id = st.text_input("Retry job_id")
    confirm_retry = st.checkbox("confirm retry", value=False)
    force_retry = st.checkbox("force retry (override idempotency check)", value=False)
    if st.button("Retry job") and confirm_retry and retry_job_id.strip():
        qp = "confirm=true"
        if force_retry:
            qp += "&force=true"
        r = api_client.post(f"/jobs/{retry_job_id.strip()}/retry?{qp}", timeout=60)
        if r.status_code != 200:
            if r.status_code == 403:
                st.error("Admin required.")
            else:
                st.error(r.text)
        else:
            st.json(r.json())

    st.subheader("3.2) Queue backlog & worker health (Redis)")
    col_q1, col_q2 = st.columns([1, 1], gap="large")
    with col_q1:
        if st.button("Load queue backlog"):
            r = api_client.get("/admin/queues", timeout=30)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.json(r.json())
    with col_q2:
        if st.button("Load workers"):
            r = api_client.get("/admin/workers", timeout=30)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.dataframe((r.json() or {}).get("workers") or [], use_container_width=True, height=220)

    st.subheader("4) Policy documents & index hygiene")
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1], gap="large")
    with col_d1:
        if st.button("List policy documents"):
            r = api_client.get("/policy/documents?limit=200", timeout=30)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.dataframe(r.json(), use_container_width=True, height=300)
    with col_d2:
        if st.button("Rebuild policy index"):
            r = api_client.post("/policy/rebuild?confirm=true", timeout=60)
            if r.status_code != 200:
                if r.status_code == 403:
                    st.error("Admin required.")
                else:
                    st.error(r.text)
            else:
                st.json(r.json())
    with col_d3:
        if st.button("Clear policy index"):
            r = api_client.post("/policy/clear?confirm=true", timeout=60)
            if r.status_code != 200:
                if r.status_code == 403:
                    st.error("Admin required.")
                else:
                    st.error(r.text)
            else:
                st.json(r.json())

    st.subheader("5) Storage cleanup (tenant)")
    dry_run = st.checkbox("dry_run", value=True)
    confirm_cleanup = st.checkbox("confirm cleanup", value=False)
    if st.button("Start cleanup job") and confirm_cleanup:
        r = api_client.post(f"/admin/cleanup?confirm=true&dry_run={'true' if dry_run else 'false'}", timeout=60)
        if r.status_code != 200:
            if r.status_code == 403:
                st.error("Admin required.")
            else:
                st.error(r.text)
        else:
            st.json(r.json())


if __name__ == "__main__":
    main()
