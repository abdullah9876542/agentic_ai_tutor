"""
frontend/app.py — Streamlit entry point

Run with: streamlit run frontend/app.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.utils.ui import (
    action_tile,
    check_backend,
    hero_pro,
    inject_theme,
    render_landing,
    render_sidebar,
    stat_row,
)

st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

for k, v in {
    "logged_in": False,
    "user_id": None,
    "username": None,
    "full_name": None,
    "role": None,
    "email": None,
    "chat_history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

client = APIClient()
check_backend(client)

if not st.session_state.logged_in:
    render_landing()
    st.stop()

render_sidebar("home")

name = st.session_state.full_name or st.session_state.username
hero_pro(
    f"Good to see you, {name}",
    "Your learning hub — jump into any module below or use the sidebar.",
    "Dashboard",
)

# Quick stats from API
summary = {}
dash = client.get_dashboard(st.session_state.user_id)
if dash["success"]:
    summary = dash["data"].get("summary", {})

stat_row([
    (str(summary.get("total_marksheets", 0)), "Marksheets", "Uploaded results", "#3b82f6"),
    (str(summary.get("total_quizzes", 0)), "Quizzes", "Completed attempts", "#ec4899"),
    (f"{summary.get('avg_quiz_score', 0)}%", "Quiz average", "Across all subjects", "#10b981"),
    (str(summary.get("tutor_sessions", 0)), "Tutor sessions", "AI chat sessions", "#06b6d4"),
])

st.markdown('<div class="ui-section-label">Quick actions</div>', unsafe_allow_html=True)

FEATURES = [
    ("📄", "rgba(59,130,246,0.22)", "Upload Marksheet", "OCR extraction from photos & PDFs.", "pages/2_Upload_Marksheet.py", True),
    ("📊", "rgba(139,92,246,0.22)", "My Analysis", "Charts, AI insights & study plan.", "pages/3_Analysis.py", False),
    ("🤖", "rgba(6,182,212,0.22)", "AI Tutor", "Chat with your adaptive tutor.", "pages/4_Tutor_Chat.py", False),
    ("🧭", "rgba(245,158,11,0.22)", "Career Roadmap", "Matches & 8-week study plan.", "pages/5_Career_Roadmap.py", False),
    ("🎯", "rgba(236,72,153,0.22)", "Quizzes", "Adaptive MCQ practice.", "pages/6_Quizzes.py", False),
    ("📈", "rgba(16,185,129,0.22)", "Dashboard", "Progress, charts & email reports.", "pages/7_Dashboard.py", False),
]

row1 = st.columns(3)
row2 = st.columns(3)
for i, (icon, bg, title, desc, page, primary) in enumerate(FEATURES):
    col = row1[i] if i < 3 else row2[i - 3]
    with col:
        action_tile(icon, bg, title, desc)
        if st.button(
            f"Open {title}",
            key=f"home_{i}",
            use_container_width=True,
            type="primary" if primary else "secondary",
        ):
            st.switch_page(page)
