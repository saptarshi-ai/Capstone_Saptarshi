"""
Streamlit Chat Interface for the Basecamp Handbook RAG System.
Connects to the FastAPI backend at http://localhost:8000.

Run: streamlit run ui/app.py
(Backend must be running: uvicorn api.main:app --reload)
"""
from pathlib import Path

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Basecamp Handbook Q&A",
    page_icon="📘",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")
    top_k = st.slider("Chunks to retrieve (top-k)", 1, 10, 5)
    st.divider()

    st.subheader("📄 Upload Document")
    uploaded = st.file_uploader("Upload .txt or .md file", type=["txt", "md"])
    if uploaded and st.button("Index Document"):
        with st.spinner("Indexing..."):
            resp = requests.post(
                f"{API_BASE}/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/plain")},
            )
        if resp.ok:
            data = resp.json()
            st.success(f"✅ Indexed {data['chunks_added']} chunks from {data['filename']}")
        else:
            st.error(f"Upload failed: {resp.text}")

    st.divider()
    if st.button("📊 View Metrics"):
        try:
            m = requests.get(f"{API_BASE}/metrics").json()
            st.json(m)
        except Exception as e:
            st.error(str(e))

    # Quick-index the handbook if not yet done
    st.divider()
    handbook_path = Path("data/temp/basecamp_handbook.md")
    if handbook_path.exists() and st.button("⚡ Index Handbook (quick start)"):
        with st.spinner("Indexing Basecamp handbook..."), open(handbook_path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/upload",
                files={"file": ("basecamp_handbook.md", f, "text/plain")},
            )
        if resp.ok:
            st.success(f"✅ Handbook indexed: {resp.json()['chunks_added']} chunks")
        else:
            st.error(resp.text)

# ── Main Chat Interface ───────────────────────────────────────────────────────
st.title("📘 Basecamp Employee Handbook Q&A")
st.caption("Ask any question about 37signals company policies, benefits, PTO, etc.")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**[{i}]** {src}")

# Chat input
if prompt := st.chat_input("Ask about benefits, PTO, insurance, sabbatical..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.chat_message("assistant"), st.spinner("Searching handbook..."):
        try:
            resp = requests.post(
                f"{API_BASE}/query",
                json={"query": prompt, "top_k": top_k},
                timeout=30,
            )
            if resp.ok:
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])
                st.markdown(answer)
                if sources:
                    with st.expander("📎 Retrieved Sources"):
                        for i, src in enumerate(sources, 1):
                            st.markdown(f"**[{i}]** {src}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
            else:
                err = f"Error {resp.status_code}: {resp.text}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
        except requests.ConnectionError:
            msg = "⚠️ Cannot reach the API. Run: `uvicorn api.main:app --reload`"
            st.error(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
