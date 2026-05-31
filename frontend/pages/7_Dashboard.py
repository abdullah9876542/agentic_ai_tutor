"""
pages/7_Dashboard.py — Student Progress Dashboard (Phase 7 + Phase 8)
Charts + Email report notification.
"""

import sys, os, html as html_lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient
from frontend.utils.ui import apply_plotly_theme, page_header, render_sidebar, require_login

st.set_page_config(page_title="Dashboard — AI Tutor", page_icon="📈", layout="wide")
require_login()
render_sidebar("dashboard")

client = APIClient()

name = st.session_state.get("full_name") or st.session_state.get("username", "")
page_header(f"{name}'s Learning Dashboard", "Your complete learning progress at a glance.")
st.divider()

# ── Load dashboard data ───────────────────────────────────────────
with st.spinner("Loading your dashboard…"):
    res = client.get_dashboard(st.session_state.user_id)

if not res["success"]:
    st.error(f"Could not load dashboard: {res['error']}")
    st.stop()

data           = res["data"]
summary        = data.get("summary", {})
subject_stats  = data.get("subject_stats", [])
quiz_history   = data.get("quiz_history", [])
quiz_subj_avg  = data.get("quiz_subject_avg", {})
weak_subjects  = data.get("weak_subjects", [])
strong_subjects= data.get("strong_subjects", [])
grades_time    = data.get("grades_over_time", [])

# ── Summary metric cards ──────────────────────────────────────────
perf      = summary.get("performance_level","N/A")
p_color   = {"Excellent":"#22c55e","Good":"#84cc16","Average":"#f59e0b",
             "Needs Improvement":"#f97316","Critical":"#ef4444"}.get(perf,"#94a3b8")

m1,m2,m3,m4,m5 = st.columns(5)
m1.markdown(
    f'<div style="background:#1e293b;border:1px solid {p_color};padding:14px;'
    f'border-radius:8px;text-align:center;">'
    f'<div style="color:{p_color};font-size:11px;font-weight:700;text-transform:uppercase;">Performance</div>'
    f'<div style="color:#f1f5f9;font-size:16px;font-weight:700;">{html_lib.escape(perf)}</div>'
    f'</div>', unsafe_allow_html=True)
m2.metric("📄 Marksheets",     summary.get("total_marksheets",0))
m3.metric("🎯 Quizzes Done",   summary.get("total_quizzes",0))
m4.metric("📊 Avg Quiz Score", f"{summary.get('avg_quiz_score',0)}%")
m5.metric("🤖 Tutor Sessions", summary.get("tutor_sessions",0))

st.divider()

# ── Row 1: Subject performance + breakdown ────────────────────────
col_chart1, col_summary = st.columns([3, 1])

with col_chart1:
    st.markdown("#### 📊 Subject Performance")
    if subject_stats:
        df_sub = pd.DataFrame(subject_stats).sort_values("percentage", ascending=False)
        df_sub["Tier"] = df_sub["percentage"].apply(
            lambda x: "Strong" if x>=70 else ("Average" if x>=50 else "Weak"))
        fig = px.bar(df_sub, x="subject", y="percentage", color="Tier",
                     color_discrete_map={"Strong":"#22c55e","Average":"#f59e0b","Weak":"#ef4444"},
                     text="percentage",
                     labels={"subject":"Subject","percentage":"Score %"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(xaxis_tickangle=-30, height=350, yaxis=dict(range=[0, 115]))
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
    else:
        st.info("Upload a marksheet to see subject performance.")

with col_summary:
    st.markdown("#### 📋 Subject Summary")
    if weak_subjects:
        st.markdown("**🔴 Needs Work:**")
        for s in weak_subjects:
            st.markdown(f"- {s}")
    if strong_subjects:
        st.markdown("**🟢 Strong:**")
        for s in strong_subjects:
            st.markdown(f"- {s}")
    if not weak_subjects and not strong_subjects:
        st.info("Run AI Analysis to see subject breakdown.")

st.divider()

# ── Row 2: Quiz chart + Progress over time ────────────────────────
col_quiz, col_prog = st.columns(2)

with col_quiz:
    st.markdown("#### 🎯 Quiz Performance by Subject")
    if quiz_subj_avg:
        df_qz = pd.DataFrame([
            {"subject":k,"avg_score":v} for k,v in quiz_subj_avg.items()])
        fig2 = px.bar(df_qz, x="subject", y="avg_score",
                      color="avg_score",
                      color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                      range_color=[0,100], text="avg_score",
                      labels={"subject":"Subject","avg_score":"Average %"})
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(height=320, coloraxis_showscale=False, yaxis=dict(range=[0, 115]))
        st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)
    else:
        st.info("Complete some quizzes to see your performance here.")

with col_prog:
    st.markdown("#### 📈 Grade Progress Over Time")
    if len(grades_time) >= 2:
        df_prog = pd.DataFrame(grades_time)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_prog["date"], y=df_prog["average"],
            mode="lines+markers",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=8, color="#6366f1"),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
        ))
        fig3.update_layout(height=320, yaxis=dict(range=[0, 110]))
        st.plotly_chart(apply_plotly_theme(fig3), use_container_width=True)
    elif grades_time:
        st.info("Upload more marksheets over time to track progress.")
    else:
        st.info("Upload marksheets to track your grade progress.")

st.divider()

# ── Recent quiz history ───────────────────────────────────────────
if quiz_history:
    st.markdown("#### 📋 Recent Quiz Attempts")
    for q in list(reversed(quiz_history))[:10]:
        pct   = q["percentage"]
        color = "#22c55e" if pct>=70 else ("#f59e0b" if pct>=50 else "#ef4444")
        bar_w = int(pct)
        st.markdown(
            f'<div style="background:#1e293b;border:1px solid #334155;border-radius:6px;'
            f'padding:10px 14px;margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
            f'<span style="color:#f1f5f9;font-weight:600;">{html_lib.escape(str(q["subject"]))}</span>'
            f'<span style="color:{color};font-weight:700;">{q["score"]}/{q["total"]} ({pct}%)</span>'
            f'<span style="color:#64748b;font-size:12px;">{q["attempted_at"]}</span>'
            f'</div>'
            f'<div style="background:#334155;border-radius:3px;height:4px;">'
            f'<div style="background:{color};width:{bar_w}%;height:4px;border-radius:3px;"></div>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# PHASE 8 — Email Notification
# ══════════════════════════════════════════════════════════════════

st.markdown("## 📧 Send Progress Report by Email")
st.markdown(
    "Send a comprehensive performance report to the student's registered email "
    "so parents and guardians can stay informed about their ward's academic performance, "
    "quiz results, AI tutor sessions, and study recommendations."
)
st.markdown("")

user_email = st.session_state.get("email", "")

col_info, col_content = st.columns([1, 1])

with col_info:
    st.markdown(
        f'<div style="background:#1e293b;border:1px solid #334155;'
        f'padding:20px;border-radius:8px;">'
        f'<div style="color:#94a3b8;font-size:12px;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Report will be sent to</div>'
        f'<div style="color:#f1f5f9;font-size:17px;font-weight:600;">📬 {html_lib.escape(user_email or "No email found")}</div>'
        f'<div style="color:#64748b;font-size:13px;margin-top:6px;">'
        f'This is the email address used during registration on the platform.</div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown(
        '<div style="background:#0f172a;border:1px solid #334155;padding:16px;border-radius:8px;">'
        '<div style="color:#818cf8;font-size:13px;font-weight:700;margin-bottom:8px;">⚙️ Email Setup Required</div>'
        '<div style="color:#94a3b8;font-size:13px;line-height:1.6;">'
        'Add these to your <strong style="color:#f1f5f9;">.env</strong> file:<br>'
        '<code style="color:#86efac;">EMAIL_SENDER</code> — your Gmail address<br>'
        '<code style="color:#86efac;">EMAIL_PASSWORD</code> — Gmail App Password<br>'
        'See <strong style="color:#f1f5f9;">.env.example</strong> for full instructions.'
        '</div>'
        '</div>', unsafe_allow_html=True)

with col_content:
    st.markdown("**📄 The report email includes:**")
    items = [
        "Overall performance level and AI summary",
        "Subject-wise scores in a table",
        "Weak, Average, and Strong subject breakdown",
        "Personalised AI study recommendations",
        "Recent quiz results and scores",
        "Number of AI tutor sessions completed",
        "Recommended career path",
        "3 immediate action items",
        "Personalised motivational note",
    ]
    for item in items:
        st.markdown(f"✅ {item}")

st.markdown("")

# ── Preview before sending ────────────────────────────────────────
with st.expander("👁️ Preview Report Data Before Sending"):
    with st.spinner("Loading report preview…"):
        prev = client.get_report_preview(st.session_state.user_id)
    if prev["success"]:
        report_data = prev["data"].get("report", {})
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown("**Performance Level:**")
            st.markdown(f"→ {report_data.get('performance_level','N/A')}")
            st.markdown("**Quizzes:**")
            st.markdown(f"→ {report_data.get('total_quizzes',0)} taken, avg {report_data.get('avg_quiz_score',0)}%")
        with col_p2:
            st.markdown("**Weak Subjects:**")
            for s in report_data.get("weak_subjects", []):
                st.markdown(f"- {s}")
            if not report_data.get("weak_subjects"):
                st.markdown("→ None")
        with col_p3:
            st.markdown("**Strong Subjects:**")
            for s in report_data.get("strong_subjects", []):
                st.markdown(f"- {s}")
            if not report_data.get("strong_subjects"):
                st.markdown("→ None")
    else:
        st.warning(f"Could not load preview: {prev['error']}")

st.markdown("")

# ── Send button ───────────────────────────────────────────────────
send_col, _ = st.columns([2, 3])
with send_col:
    send_clicked = st.button(
        "📤 Send Progress Report to Parent / Guardian",
        type="primary",
        use_container_width=True,
    )

if send_clicked:
    if perf == "N/A":
        st.warning("⚠️ Please run the AI Analysis first so the report has meaningful content.")
        if st.button("📊 Go to Analysis", use_container_width=False):
            st.switch_page("pages/3_Analysis.py")
    elif not user_email:
        st.error("❌ No email address found. Please contact support.")
    else:
        with st.spinner(f"Sending progress report to {user_email}…"):
            send_res = client.send_report_email(st.session_state.user_id)

        if send_res["success"]:
            sent_to = send_res["data"].get("sent_to", user_email)
            st.success(
                f"✅ Progress report sent successfully to **{sent_to}**! "
                "The parent / guardian should receive it within a few minutes."
            )
            st.balloons()
        else:
            st.error(f"❌ {send_res['error']}")

st.divider()

# ── Quick actions ─────────────────────────────────────────────────
st.markdown("#### 🚀 Quick Actions")
c1,c2,c3,c4 = st.columns(4)
with c1:
    if st.button("📄 Upload Marksheet", use_container_width=True):
        st.switch_page("pages/2_Upload_Marksheet.py")
with c2:
    if st.button("🤖 Start Tutoring", use_container_width=True, type="primary"):
        st.switch_page("pages/4_Tutor_Chat.py")
with c3:
    if st.button("🎯 Take a Quiz", use_container_width=True):
        st.switch_page("pages/6_Quizzes.py")
with c4:
    if st.button("🧭 Career Guidance", use_container_width=True):
        st.switch_page("pages/5_Career_Roadmap.py")
