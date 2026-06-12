# frontend/app.py

import streamlit as st
import requests
import os

# Reads from Streamlit secrets (cloud) → env var → localhost fallback
API = (
    st.secrets.get("BACKEND_URL")
    or os.getenv("BACKEND_URL")
    or "http://localhost:8000/api"
)

st.set_page_config(page_title="Study Agent", page_icon="📚", layout="wide")
st.title("📚 Study Agent")

# --- Sidebar ---
with st.sidebar:
    st.header("Upload Document")
    uploaded = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])

    if uploaded:
        if st.button("Upload & Index", type="primary"):
            with st.spinner("Indexing..."):
                try:
                    resp = requests.post(
                        f"{API}/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                    )
                    if resp.ok:
                        data = resp.json()
                        st.success(f"Indexed **{data['filename']}** — {data['chunks_stored']} chunks")
                        st.session_state.pop("doc_list", None)
                    else:
                        st.error(resp.json().get("detail", "Upload failed"))
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend.")

    st.divider()

    # Document selector (shared by both tabs)
    st.subheader("Active Document")
    if "doc_list" not in st.session_state:
        try:
            resp = requests.get(f"{API}/documents")
            st.session_state.doc_list = resp.json().get("documents", []) if resp.ok else []
        except requests.exceptions.ConnectionError:
            st.session_state.doc_list = []

    doc_options = ["All Documents"] + st.session_state.doc_list
    active_doc = st.selectbox("Search within:", options=doc_options)
    doc_filter = None if active_doc == "All Documents" else active_doc

    st.divider()
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Backend: `uvicorn backend.app:app --reload`")


# --- Tabs ---
chat_tab, quiz_tab = st.tabs(["💬 Chat", "🧠 Quiz"])


# ── Chat Tab ─────────────────────────────────────────────────────────────────
with chat_tab:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources", expanded=False):
                    for s in msg["sources"]:
                        st.caption(f"• {s['id']}  (score: {s['score']})")

    question = st.chat_input("Ask a question...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]
                try:
                    resp = requests.post(f"{API}/query", json={
                        "question": question,
                        "history": history,
                        "doc_filter": doc_filter,
                        "k": 5,
                    })
                    if resp.ok:
                        data = resp.json()
                        answer = data["answer"]
                        sources = data.get("sources", [])
                    else:
                        answer = f"Error: {resp.json().get('detail', 'Unknown error')}"
                        sources = []
                except requests.exceptions.ConnectionError:
                    answer = "Cannot connect to backend. Is the server running?"
                    sources = []

            st.markdown(answer)
            if sources:
                with st.expander("Sources", expanded=False):
                    for s in sources:
                        st.caption(f"• {s['id']}  (score: {s['score']})")

        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})


# ── Quiz Tab ──────────────────────────────────────────────────────────────────
with quiz_tab:
    st.subheader("Generate a Quiz")
    st.caption("The quiz is generated from your uploaded document. Select one from the sidebar for best results.")

    num_q = st.slider("Number of questions", min_value=3, max_value=10, value=5)

    if st.button("Generate Quiz", type="primary"):
        with st.spinner("Generating questions..."):
            try:
                resp = requests.post(f"{API}/quiz", json={
                    "doc_filter": doc_filter,
                    "num_questions": num_q,
                })
                if resp.ok:
                    st.session_state.quiz = resp.json().get("questions", [])
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                else:
                    st.error(resp.json().get("detail", "Quiz generation failed"))
                    st.session_state.quiz = []
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")
                st.session_state.quiz = []

    # Render quiz if available
    if st.session_state.get("quiz"):
        questions = st.session_state.quiz
        submitted = st.session_state.get("quiz_submitted", False)

        st.divider()

        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            options = q.get("options", {})
            choices = [f"{k}: {v}" for k, v in options.items()]

            if not submitted:
                selected = st.radio(
                    label=f"q{i}",
                    options=choices,
                    index=None,
                    label_visibility="collapsed",
                    key=f"q_{i}",
                )
                if selected:
                    st.session_state.quiz_answers[i] = selected[0]  # store "A", "B", etc.
            else:
                correct = q.get("answer", "")
                user_ans = st.session_state.quiz_answers.get(i)
                for choice in choices:
                    letter = choice[0]
                    if letter == correct:
                        st.markdown(f"✅ **{choice}**")
                    elif letter == user_ans and user_ans != correct:
                        st.markdown(f"❌ ~~{choice}~~")
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{choice}")
                st.caption(f"_{q.get('explanation', '')}_")

            st.markdown("")

        if not submitted:
            if st.button("Submit Answers", type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            # Score
            correct_count = sum(
                1 for i, q in enumerate(questions)
                if st.session_state.quiz_answers.get(i) == q.get("answer")
            )
            total = len(questions)
            pct = int(correct_count / total * 100)

            if pct == 100:
                result_msg = f"🏆 Perfect score! {correct_count}/{total}"
            elif pct >= 70:
                result_msg = f"👍 Good job! {correct_count}/{total} ({pct}%)"
            else:
                result_msg = f"📖 Keep studying! {correct_count}/{total} ({pct}%)"

            st.success(result_msg)

            if st.button("Try Again"):
                st.session_state.quiz = []
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()
