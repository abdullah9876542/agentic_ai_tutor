"""
pages/3_Analysis.py — Phase 2 (grades/charts) + Phase 3 (AI Analyzer Agent)

BUG FIX: Replaced list comprehensions used for side effects with proper for loops.
         In Streamlit 1.35+, st.markdown() returns a DeltaGenerator object.
         A list comprehension [st.markdown() for x in items] creates a list of
         DeltaGenerators which Streamlit auto-renders as raw object strings.
         Fix: use plain for loops — they execute side effects without a return value.
"""

import sys, os, html as html_lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.utils.api_client import APIClient
from frontend.utils.ui import apply_plotly_theme, page_header, render_sidebar, require_login

st.set_page_config(page_title="My Analysis — AI Tutor", page_icon="📊", layout="wide")
require_login()
render_sidebar("analysis")

client = APIClient()
page_header("My Grade Analysis", "Charts, subject breakdown, and AI-powered study recommendations.")
st.divider()

# ══════════════════════════════════════════════════════════════════
# PHASE 2 — Grades, chart, table, weak/strong
# ══════════════════════════════════════════════════════════════════

grades = st.session_state.get("latest_grades")
if not grades:
    res = client.get_marksheets(st.session_state.user_id)
    if res["success"] and res["data"]["marksheets"]:
        latest = res["data"]["marksheets"][0]
        grades = latest.get("grades", [])
        st.session_state.latest_grades = grades
        st.session_state.marksheet_id  = latest.get("id")
    else:
        st.info("No marksheet found. Please upload one first.")
        if st.button("📄 Upload Marksheet", type="primary"):
            st.switch_page("pages/2_Upload_Marksheet.py")
        st.stop()

if not grades:
    st.warning("No grades found. Please upload a marksheet.")
    if st.button("📄 Upload Marksheet"):
        st.switch_page("pages/2_Upload_Marksheet.py")
    st.stop()

df = pd.DataFrame(grades)

def calc_pct(row):
    try:
        if row.get("score") is not None and row.get("max_score"):
            return round((row["score"] / row["max_score"]) * 100, 1)
    except Exception:
        pass
    return None

df["percentage"] = df.apply(calc_pct, axis=1)
df_valid = df.dropna(subset=["percentage"])

if not df_valid.empty:
    avg   = round(df_valid["percentage"].mean(), 1)
    best  = df_valid.loc[df_valid["percentage"].idxmax()]
    worst = df_valid.loc[df_valid["percentage"].idxmin()]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📚 Total Subjects", len(grades))
    m2.metric("📊 Average Score",  f"{avg}%")
    m3.metric("🏆 Best Subject",   f"{best['subject']}",  f"{best['percentage']}%")
    m4.metric("⚠️ Needs Work",     f"{worst['subject']}", f"{worst['percentage']}%")

st.divider()
col_chart, col_table = st.columns([3, 2])

with col_chart:
    st.markdown("#### Score by Subject")
    if not df_valid.empty:
        df_plot = df_valid.copy()
        df_plot["Performance"] = df_plot["percentage"].apply(
            lambda x: "Strong" if x >= 70 else ("Average" if x >= 50 else "Weak"))
        fig = px.bar(
            df_plot, x="subject", y="percentage", color="Performance",
            color_discrete_map={"Strong": "#22c55e", "Average": "#f59e0b", "Weak": "#ef4444"},
            labels={"subject": "Subject", "percentage": "Score %"},
            text="percentage",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(xaxis_tickangle=-30, showlegend=True, height=400)
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)
    else:
        st.info("No numeric scores to chart.")

with col_table:
    st.markdown("#### Grade Summary")
    display_df = df.rename(columns={
        "subject": "Subject", "score": "Score",
        "max_score": "Max", "grade": "Grade", "percentage": "%"
    })
    st.dataframe(display_df[["Subject", "Score", "Max", "Grade", "%"]],
                 use_container_width=True, hide_index=True)

st.divider()

# ── Weak / Average / Strong breakdown ─────────────────────────────
if not df_valid.empty:
    weak    = df_valid[df_valid["percentage"] < 50]["subject"].tolist()
    average = df_valid[(df_valid["percentage"] >= 50) & (df_valid["percentage"] < 70)]["subject"].tolist()
    strong  = df_valid[df_valid["percentage"] >= 70]["subject"].tolist()

    cw, ca, cs = st.columns(3)

    with cw:
        st.markdown("#### 🔴 Needs Improvement")
        if weak:
            for s in weak:
                st.markdown(f"- {s}")
        else:
            st.success("No weak subjects!")

    with ca:
        st.markdown("#### 🟡 Average")
        if average:
            for s in average:
                st.markdown(f"- {s}")
        else:
            st.info("None")

    with cs:
        st.markdown("#### 🟢 Strong")
        if strong:
            for s in strong:
                st.markdown(f"- {s}")
        else:
            st.info("None")

# ══════════════════════════════════════════════════════════════════
# PHASE 3 — AI Analyzer Agent
# ══════════════════════════════════════════════════════════════════

st.divider()
st.markdown("## 🤖 AI Performance Analysis")
st.caption("Powered by the AI Analyzer Agent — deep insights, patterns, and personalised study recommendations.")

analysis     = st.session_state.get("latest_analysis")
marksheet_id = st.session_state.get("marksheet_id")

if not analysis:
    res = client.get_latest_analysis(st.session_state.user_id)
    if res["success"] and res["data"].get("analysis"):
        analysis = res["data"]["analysis"]
        st.session_state.latest_analysis = analysis

col_btn, col_info = st.columns([2, 3])
with col_btn:
    run_clicked = st.button(
        "🔄 Re-run AI Analysis" if analysis else "🚀 Run AI Analysis",
        type="primary", use_container_width=True,
    )
with col_info:
    if analysis:
        st.info("✅ Analysis loaded. Click **Re-run** to refresh with the latest marksheet.")
    else:
        st.info("Click **Run AI Analysis** to get deep insights on your performance.")

if run_clicked:
    with st.spinner("The Analyzer Agent is processing your grades… this takes about 15–20 seconds."):
        res = client.run_analysis(
            user_id      = st.session_state.user_id,
            marksheet_id = marksheet_id,
        )
    if res["success"]:
        analysis = res["data"]["analysis"]
        st.session_state.latest_analysis = analysis
        st.success("✅ Analysis complete!")
        st.rerun()
    else:
        st.error(f"❌ {res['error']}")

if not analysis:
    st.stop()

st.divider()

# ── Overall summary card ──────────────────────────────────────────
perf_level = analysis.get("performance_level", "")
perf_color = {
    "Excellent":         "#22c55e",
    "Good":              "#84cc16",
    "Average":           "#f59e0b",
    "Needs Improvement": "#f97316",
    "Critical":          "#ef4444",
}.get(perf_level, "#94a3b8")

st.markdown(
    f'<div style="background:#1e293b;border-left:5px solid {perf_color};'
    f'padding:16px 20px;border-radius:8px;margin-bottom:4px;">'
    f'<span style="color:{perf_color};font-size:12px;font-weight:700;'
    f'letter-spacing:1px;text-transform:uppercase;">'
    f'Overall Performance — {html_lib.escape(perf_level)}</span>'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown(f"> {analysis.get('summary', '')}")

# ── Patterns ──────────────────────────────────────────────────────
patterns = analysis.get("patterns", [])
if patterns:
    st.markdown("#### 🔍 Performance Patterns Detected")
    for i, p in enumerate(patterns, 1):
        st.markdown(
            f'<div style="background:#0f172a;border:1px solid #334155;padding:12px 16px;'
            f'border-radius:6px;margin-bottom:8px;line-height:1.6;">'
            f'<span style="color:#818cf8;font-weight:700;">Pattern {i}:</span> '
            f'<span style="color:#cbd5e1;">{html_lib.escape(str(p))}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ── Subject recommendations ───────────────────────────────────────
recommendations = analysis.get("study_recommendations", {})
priority_order  = analysis.get("priority_study_order", [])

if recommendations:
    st.markdown("#### 📚 Subject-by-Subject Study Recommendations")
    st.caption("Ordered by urgency — most critical subjects first.")

    ordered = list(dict.fromkeys(
        [s for s in priority_order if s in recommendations]
        + list(recommendations.keys())
    ))

    for idx, subject in enumerate(ordered):
        rec = recommendations[subject]

        pct_val = None
        for g in grades:
            if g.get("subject", "").lower() == subject.lower():
                if g.get("score") is not None and g.get("max_score"):
                    pct_val = round((g["score"] / g["max_score"]) * 100, 1)
                break

        if pct_val is not None:
            if pct_val < 50:
                badge_color, badge_label = "#ef4444", f"{pct_val}% · Needs Work"
            elif pct_val < 70:
                badge_color, badge_label = "#f59e0b", f"{pct_val}% · Average"
            else:
                badge_color, badge_label = "#22c55e", f"{pct_val}% · Strong"
        else:
            badge_color, badge_label = "#64748b", "Score N/A"

        priority_badge = ""
        if idx == 0:
            priority_badge = (
                '<span style="background:#ef4444;color:white;font-size:10px;'
                'padding:2px 8px;border-radius:10px;margin-left:8px;">TOP PRIORITY</span>'
            )
        elif idx == 1:
            priority_badge = (
                '<span style="background:#f97316;color:white;font-size:10px;'
                'padding:2px 8px;border-radius:10px;margin-left:8px;">HIGH PRIORITY</span>'
            )

        st.markdown(
            f'<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;'
            f'padding:14px 18px;margin-top:10px;">'
            f'<div style="margin-bottom:8px;">'
            f'<span style="color:#f1f5f9;font-size:15px;font-weight:700;">'
            f'{html_lib.escape(subject)}</span>'
            f'<span style="background:{badge_color};color:white;font-size:11px;'
            f'padding:2px 10px;border-radius:10px;margin-left:10px;">'
            f'{html_lib.escape(badge_label)}</span>'
            f'{priority_badge}</div>'
            f'<div style="color:#94a3b8;font-size:14px;line-height:1.6;">'
            f'{html_lib.escape(str(rec))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ── Priority order ────────────────────────────────────────────────
if priority_order:
    st.markdown("#### 🎯 Recommended Study Priority Order")
    max_cols = min(len(priority_order), 5)
    cols = st.columns(max_cols)
    for i, subject in enumerate(priority_order):
        bg     = "#ef4444" if i == 0 else ("#f97316" if i == 1 else "#1e293b")
        border = "" if i < 2 else "border:1px solid #334155;"
        with cols[i % max_cols]:
            st.markdown(
                f'<div style="background:{bg};{border}padding:10px 12px;border-radius:8px;'
                f'text-align:center;margin-bottom:8px;">'
                f'<div style="color:rgba(255,255,255,0.6);font-size:11px;">#{i + 1}</div>'
                f'<div style="color:white;font-weight:700;font-size:13px;">'
                f'{html_lib.escape(subject)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.divider()

# ── Improvement potential + motivational note ─────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### 📈 Improvement Potential")
    st.markdown(
        f'<div style="background:#172554;border:1px solid #1e40af;padding:14px;'
        f'border-radius:8px;color:#93c5fd;font-size:14px;line-height:1.6;">'
        f'{html_lib.escape(str(analysis.get("estimated_improvement_potential", "")))}'
        f'</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown("#### 💬 A Note For You")
    st.markdown(
        f'<div style="background:#14532d;border:1px solid #166534;padding:14px;'
        f'border-radius:8px;color:#86efac;font-size:14px;line-height:1.6;font-style:italic;">'
        f'"{html_lib.escape(str(analysis.get("motivational_note", "")))}"'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()
st.markdown("#### What would you like to do next?")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🤖 Start AI Tutoring", use_container_width=True, type="primary"):
        st.switch_page("pages/4_Tutor_Chat.py")
with c2:
    if st.button("🧭 View Career Guidance", use_container_width=True):
        st.switch_page("pages/5_Career_Roadmap.py")
with c3:
    if st.button("📄 Upload New Marksheet", use_container_width=True):
        st.switch_page("pages/2_Upload_Marksheet.py")
