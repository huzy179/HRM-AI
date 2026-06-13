from __future__ import annotations

import streamlit as st
from frontend.ui_utils import apply_premium_style, render_auth_gate


def main() -> None:
    st.set_page_config(
        page_title="HRM AI - Phase 1",
        page_icon="📋",
        layout="wide",
    )
    apply_premium_style()
    # if not render_auth_gate():
    #     return

    st.title("🚀 HRM AI — Premium Recruitment & Assistant Suite")
    st.caption("Hệ thống quản lý tuyển dụng thông minh tích hợp AI (Local Ollama, Offline-first).")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### 🧾 CV Screening & Automation
            *   **Sàng lọc thông minh**: Phân tích, OCR và xếp hạng ứng viên dựa trên độ tương thích ngữ nghĩa và các tiêu chí kinh nghiệm/kỹ năng của JD.
            *   **Biểu đồ Radar Match**: Trực quan hóa độ phù hợp kỹ năng của ứng viên so với JD.
            *   **Email Automation**: Tự sinh thư mời phỏng vấn, Job Offer hoặc thư từ chối cá nhân hóa bằng Llama3.
            *   👉 *Mở trang **2_CV_Screening_API** ở sidebar bên trái để bắt đầu.*
            """
        )
        
    with col2:
        st.markdown(
            """
            ### 📚 Policy Chatbot & RAG
            *   **Tra cứu chính sách**: Hỏi đáp và đối chiếu nguồn trích dẫn từ các tài liệu nội bộ (.pdf, .txt, .docx, .md).
            *   **Advanced Retrieval**: Reranking lai (Dense-Sparse) tăng độ chính xác trích dẫn.
            *   **Streaming & History**: Trò chuyện thời gian thực mượt mà và ghi nhớ ngữ cảnh hội thoại.
            *   👉 *Mở trang **9_Policy_Chat_API** ở sidebar bên trái để bắt đầu.*
            """
        )


if __name__ == "__main__":
    main()
