from __future__ import annotations

import os
import json
from typing import List

import streamlit as st
from frontend import api_client
from frontend.ui_utils import apply_premium_style, render_auth_gate

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def main() -> None:
    st.set_page_config(page_title="Policy Chat & RAG", page_icon="📚", layout="wide")
    apply_premium_style()
    # if not render_auth_gate():
    #     return

    # Title with beautiful gradient
    st.title("📚 Policy Chatbot & RAG")
    st.caption(f"API Endpoint: `{API_BASE_URL}`")

    # Initializing session states for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar for Document Management
    with st.sidebar:
        st.header("⚙️ Document Management")
        
        # Ingestion Section
        with st.expander("📥 Upload & Ingest Documents", expanded=True):
            files = st.file_uploader(
                "Upload policy Documents (PDF, TXT, DOCX, MD)", 
                type=["pdf", "txt", "docx", "md"], 
                accept_multiple_files=True,
                key="policy_uploader"
            )
            if st.button("Start Ingest", use_container_width=True) and files:
                with st.spinner("Uploading and processing documents..."):
                    payload_files = [("files", (f.name, f.getvalue(), "application/octet-stream")) for f in files]
                    try:
                        r = api_client.post("/policy/ingest", files=payload_files, timeout=300)
                        if r.status_code == 200:
                            st.success("Successfully enqueued ingestion job!")
                            st.json(r.json())
                        else:
                            st.error(f"Error: {r.status_code} - {r.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to API: {e}")
        
        # Document List Section
        with st.expander("📄 Ingested Documents", expanded=False):
            if st.button("Refresh Document List", use_container_width=True):
                try:
                    r = api_client.get("/policy/documents", timeout=30)
                    if r.status_code == 200:
                        st.session_state.policy_docs = r.json()
                    else:
                        st.error("Failed to fetch documents")
                except Exception as e:
                    st.error(f"Error: {e}")
            
            docs = st.session_state.get("policy_docs", [])
            if not docs:
                try:
                    r = api_client.get("/policy/documents", timeout=30)
                    if r.status_code == 200:
                        docs = r.json()
                        st.session_state.policy_docs = docs
                except Exception:
                    pass
            
            if "selected_docs" not in st.session_state:
                st.session_state.selected_docs = []

            if docs:
                st.markdown("Select documents to query:")
                selected_ids = []
                for doc in docs:
                    status_color = "🟢" if doc.get("ingest_status") == "OK" else ("🟡" if doc.get("ingest_status") == "PENDING" else "🔴")
                    doc_id = str(doc.get("id"))
                    is_checked = st.checkbox(
                        f"{status_color} {doc.get('filename')}",
                        value=doc_id in st.session_state.selected_docs,
                        key=f"check_{doc_id}"
                    )
                    if is_checked:
                        selected_ids.append(doc_id)
                    if doc.get("error"):
                        st.caption(f"Error: {doc.get('error')}")
                st.session_state.selected_docs = selected_ids
            else:
                st.info("No documents enqueued yet.")
                
        # Advanced / Danger Zone
        with st.expander("⚠️ Danger Zone", expanded=False):
            confirm_clear = st.checkbox("Confirm Clear Index")
            if st.button("Clear Vector Index", type="primary", use_container_width=True, disabled=not confirm_clear):
                try:
                    r = api_client.post("/policy/clear?confirm=true", timeout=30)
                    if r.status_code == 200:
                        st.success("Clear index job enqueued.")
                        st.session_state.messages = []  # Clear history as well
                        st.rerun()
                    else:
                        st.error(r.text)
                except Exception as e:
                    st.error(str(e))
                    
            confirm_rebuild = st.checkbox("Confirm Rebuild Index")
            if st.button("Rebuild Index", use_container_width=True, disabled=not confirm_rebuild):
                try:
                    r = api_client.post("/policy/rebuild?confirm=true", timeout=30)
                    if r.status_code == 200:
                        st.success("Rebuild index job enqueued.")
                    else:
                        st.error(r.text)
                except Exception as e:
                    st.error(str(e))

    # Main Chat Area
    # Control Options
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        st.subheader("💬 Chat with HR Policy Assistant")
    with col_ctrl2:
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Display Chat Messages
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        citations = msg.get("citations", [])
        
        if role == "user":
            st.markdown(f'<div class="chat-bubble-user">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-agent">{content}</div>', unsafe_allow_html=True)
            if citations:
                with st.expander("🔍 Citations & Evidence Sources", expanded=False):
                    for i, cit in enumerate(citations):
                        st.markdown(
                            f'<div class="citation-card">'
                            f'<span class="citation-tag">Source: {cit.get("source")} | Match: {round(cit.get("score", 0)*100, 1)}%</span><br/>'
                            f'"{cit.get("snippet")}"'
                            f'</div>',
                            unsafe_allow_html=True
                        )

    # Chat Input
    query = st.chat_input("Ask a question about company guidelines...")
    if query:
        # Display user message instantly
        st.markdown(f'<div class="chat-bubble-user">{query}</div>', unsafe_allow_html=True)
        
        # Build history payload
        # Send history excluding citations to keep request lightweight
        history_payload = []
        for msg in st.session_state.messages:
            history_payload.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            
        try:
            # Add current question to messages first
            st.session_state.messages.append({"role": "user", "content": query})
            
            selected_docs = st.session_state.get("selected_docs", [])
            
            # Call Policy Chat API with history and doc_ids filter
            r = api_client.post_stream(
                "/policy/chat/stream", 
                json={
                    "query": query, 
                    "k": 5,
                    "history": history_payload,
                    "doc_ids": selected_docs if selected_docs else None
                }, 
                timeout=300
            )
            
            if r.status_code == 200:
                citations = []
                full_answer = ""
                
                # Write to stream
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    def generate_chunks():
                        nonlocal citations, full_answer
                        lines_iter = r.iter_lines()
                        
                        # Read first line for citations
                        try:
                            first_line = next(lines_iter).decode('utf-8')
                            if first_line.startswith("CITATIONS: "):
                                citations = json.loads(first_line[11:])
                        except Exception:
                            pass
                            
                        # Stream the rest
                        for line in lines_iter:
                            decoded = line.decode('utf-8')
                            full_answer += decoded
                            placeholder.markdown(full_answer + "▌")
                            yield decoded
                            
                    # Consume the generator to trigger updates
                    list(generate_chunks())
                    placeholder.markdown(full_answer)
                
                # Store agent reply
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_answer,
                    "citations": citations
                })
                st.rerun()
            else:
                st.error(f"Error from API: {r.status_code} - {r.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")


if __name__ == "__main__":
    main()
