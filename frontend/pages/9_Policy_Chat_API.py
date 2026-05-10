from __future__ import annotations

import os
from typing import List

import requests
import streamlit as st


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def main() -> None:
    st.set_page_config(page_title="Policy Chat", page_icon="📚", layout="wide")
    st.title("📚 Policy Chat (Phase 2)")
    st.caption(f"API: `{API_BASE_URL}`")

    st.subheader("1) Ingest policy documents")
    files = st.file_uploader("Upload policy PDFs/TXTs", type=["pdf", "txt"], accept_multiple_files=True)
    if st.button("Ingest") and files:
        payload_files = [("files", (f.name, f.getvalue(), "application/octet-stream")) for f in files]
        r = requests.post(_api("/policy/ingest"), files=payload_files, timeout=300)
        st.json(r.json())

    st.subheader("2) Ask a question")
    query = st.text_input("Question", value="Quy định nghỉ phép như thế nào?")
    k = st.slider("Top K citations", min_value=3, max_value=10, value=5)
    if st.button("Ask"):
        r = requests.post(_api("/policy/chat"), json={"query": query, "k": k}, timeout=300)
        data = r.json()
        st.write("**Answer**")
        st.write(data.get("answer", ""))
        st.write("**Citations**")
        st.json(data.get("citations", []))


if __name__ == "__main__":
    main()

