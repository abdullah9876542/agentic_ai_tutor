"""
pages/4_Tutor_Chat.py — AI Tutor Chat (Phase 5)
LangGraph-powered adaptive tutor with subject selector and session persistence.
"""

import sys, os, html as html_lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.utils.ui import page_header, render_sidebar, require_login

st.set_page_config(page_title="AI Tutor — Chat", page_icon="🤖", layout="wide")
require_login()
render_sidebar("tutor")

# ── Session state defaults ────────────────────────────────────────
for k, v in {"tutor_session_id": None, "tutor_messages": [],
              "tutor_subject": None, "tutor_weak_subjects": [],
              "tutor_all_subjects": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

client = APIClient()

with st.sidebar:
    if st.session_state.tutor_session_id:
        st.markdown("**Active session**")
        st.caption(f"#{st.session_state.tutor_session_id} · {st.session_state.tutor_subject}")
        st.caption(f"{len(st.session_state.tutor_messages)} messages")
        if st.button("End Session", use_container_width=True):
            st.session_state.tutor_session_id = None
            st.session_state.tutor_messages   = []
            st.session_state.tutor_subject    = None
            st.rerun()
        st.divider()

page_header("AI Tutor", "Personalised tutoring sessions powered by LangGraph.")

# ═══════════════════════════════════════════════════════════════════
# SCREEN 1 — No active session: Subject selector
# ═══════════════════════════════════════════════════════════════════

if not st.session_state.tutor_session_id:
    st.markdown("Select a subject and start a personalised tutoring session.")
    st.divider()

    # Load subjects if not cached
    if not st.session_state.tutor_all_subjects:
        with st.spinner("Loading your subjects…"):
            res = client.get_weak_subjects(st.session_state.user_id)
        if res["success"]:
            st.session_state.tutor_weak_subjects = res["data"].get("weak_subjects", [])
            st.session_state.tutor_all_subjects  = res["data"].get("all_subjects", [])

    weak    = st.session_state.tutor_weak_subjects
    all_sub = st.session_state.tutor_all_subjects

    col_left, col_right = st.columns([1, 1])

    with col_left:
        # Weak subjects as quick-start cards
        if weak:
            st.markdown("#### ⚡ Start with your weak subjects")
            st.caption("These need the most attention based on your grades.")
            for subj in weak:
                if st.button(f"📖 {subj}", key=f"weak_{subj}", use_container_width=True, type="primary"):
                    with st.spinner(f"Starting session for {subj}…"):
                        res = client.start_tutor_session(st.session_state.user_id, subj)
                    if res["success"]:
                        d = res["data"]
                        st.session_state.tutor_session_id = d["session_id"]
                        st.session_state.tutor_subject    = subj
                        st.session_state.tutor_messages   = [
                            {"role": "assistant", "content": d["greeting"]}
                        ]
                        st.rerun()
                    else:
                        st.error(f"❌ {res['error']}")

    with col_right:
        st.markdown("#### 📚 Or choose any subject")
        all_options = list(dict.fromkeys(weak + [s for s in all_sub if s not in weak]))
        if all_options:
            selected = st.selectbox("Pick a subject:", all_options)
        else:
            selected = st.text_input("Enter subject name:", placeholder="e.g. Mathematics")

        diff = st.select_slider("Difficulty:", ["Easy","Medium","Hard"], value="Medium")

        if st.button("🚀 Start Tutoring Session", type="primary", use_container_width=True):
            if not selected:
                st.warning("Please select or enter a subject.")
            else:
                with st.spinner(f"Starting session for {selected}…"):
                    res = client.start_tutor_session(st.session_state.user_id, selected)
                if res["success"]:
                    d = res["data"]
                    st.session_state.tutor_session_id = d["session_id"]
                    st.session_state.tutor_subject    = selected
                    st.session_state.tutor_messages   = [
                        {"role": "assistant", "content": d["greeting"]}
                    ]
                    st.rerun()
                else:
                    st.error(f"❌ {res['error']}")

    # ── Past sessions ─────────────────────────────────────────────
    st.divider()
    with st.expander("📂 Previous Sessions"):
        res = client.get_tutor_sessions(st.session_state.user_id)
        if res["success"]:
            sessions = res["data"].get("sessions", [])
            if sessions:
                for s in sessions[:5]:
                    st.markdown(
                        f'<div style="background:#1e293b;border:1px solid #334155;'
                        f'padding:10px 14px;border-radius:6px;margin-bottom:6px;">'
                        f'<span style="color:#f1f5f9;font-weight:700;">{html_lib.escape(str(s["subject"]))}</span>'
                        f'<span style="color:#64748b;font-size:12px;margin-left:10px;">'
                        f'{s["message_count"]} messages · {s["started_at"][:10]}</span>'
                        f'</div>', unsafe_allow_html=True)
            else:
                st.info("No previous sessions yet.")

    st.stop()


# ═══════════════════════════════════════════════════════════════════
# SCREEN 2 — Active chat session
# ═══════════════════════════════════════════════════════════════════

st.markdown(f"### 📖 Tutoring: **{st.session_state.tutor_subject}**")
st.caption(f"Session #{st.session_state.tutor_session_id} · {len(st.session_state.tutor_messages)} messages")

# ── Render chat history ───────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.tutor_messages:
        role    = msg["role"]
        content = msg["content"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content)
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)

# ── Quiz suggestion banner ────────────────────────────────────────
if st.session_state.get("suggest_quiz_subject"):
    subj = st.session_state.suggest_quiz_subject
    st.info(f"🎯 You seem to be getting the hang of **{subj}**! Want to test yourself with a quick quiz?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Yes, take a quiz!", use_container_width=True, type="primary"):
            st.session_state.quiz_prefill_subject = subj
            st.switch_page("pages/6_Quizzes.py")
    with c2:
        if st.button("❌ Not yet, keep going", use_container_width=True):
            st.session_state.suggest_quiz_subject = None
            st.rerun()

# ── Chat input ────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question, answer the tutor, or say what's confusing you…")

if user_input:
    # Immediately show the user message
    st.session_state.tutor_messages.append({"role":"user","content":user_input})

    with st.spinner("Tutor is thinking…"):
        res = client.send_tutor_message(
            session_id = st.session_state.tutor_session_id,
            user_id    = st.session_state.user_id,
            message    = user_input,
        )

    if res["success"]:
        d = res["data"]
        reply = d["response"]
        st.session_state.tutor_messages.append({"role":"assistant","content":reply})

        if d.get("suggested_quiz"):
            st.session_state.suggest_quiz_subject = st.session_state.tutor_subject
    else:
        st.session_state.tutor_messages.append({
            "role": "assistant",
            "content": f"Sorry, I had trouble responding. Please try again. ({res['error']})"
        })

    st.rerun()
