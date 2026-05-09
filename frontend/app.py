from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="HRM AI - Phase 1",
        page_icon="📋",
        layout="wide",
    )

    st.title("📋 HRM AI — Phase 1: CV Screening")
    st.caption("MVP: Upload CV (PDF) + nhập JD → parse → embeddings (Ollama) → rank.")
    st.info("Mở trang `1_CV_Screening` ở sidebar (Pages) để bắt đầu.")


if __name__ == "__main__":
    main()
