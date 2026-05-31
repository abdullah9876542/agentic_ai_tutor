"""
pages/5_Career_Roadmap.py — Career Agent frontend (Phase 4)
HTML FIX: html.escape() on all GPT text, every card is one self-contained st.markdown() call.
"""

import sys, os, html as html_lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.utils.ui import page_header, render_sidebar, require_login

st.set_page_config(page_title="Career Roadmap — AI Tutor", page_icon="🧭", layout="wide")
require_login()
render_sidebar("career")

client = APIClient()

page_header(
    "Career Guidance & Roadmap",
    "Personalised career matches and an 8-week study plan based on your grades.",
)
st.divider()

# ── Load result ───────────────────────────────────────────────────
career_result = st.session_state.get("career_result")
if not career_result:
    res = client.get_career_result(st.session_state.user_id)
    if res["success"] and res["data"].get("result"):
        career_result = res["data"]["result"]
        st.session_state.career_result = career_result

col_btn, col_info = st.columns([2, 3])
with col_btn:
    run_clicked = st.button(
        "🔄 Re-run Career Analysis" if career_result else "🚀 Generate Career Guidance",
        type="primary", use_container_width=True)
with col_info:
    if career_result:
        st.info("✅ Career guidance loaded. Click **Re-run** to regenerate.")
    else:
        st.info("Requires: marksheet uploaded ✅  +  AI Analysis completed ✅")

if run_clicked:
    with st.spinner("Career Agent is generating your personalised guidance… (~20 seconds)"):
        res = client.run_career(st.session_state.user_id)
    if res["success"]:
        career_result = res["data"]["result"]
        st.session_state.career_result = career_result
        st.success("✅ Career guidance generated!")
        st.rerun()
    else:
        st.error(f"❌ {res['error']}")
        if "nalysis" in res["error"]:
            st.info("👉 Go to **My Analysis** page and click **Run AI Analysis** first.")
            if st.button("📊 Go to Analysis"): st.switch_page("pages/3_Analysis.py")
        st.stop()

if not career_result:
    st.info("No career guidance yet. Click **Generate Career Guidance** above to get started.")
    st.stop()

# ── Education pathway ─────────────────────────────────────────────
edu = career_result.get("education_pathway", {})
grade_level = career_result.get("detected_grade_level", "")

if edu or grade_level:
    st.markdown("## 🎓 Education Pathway")
    cols_edu = st.columns([1, 2])
    with cols_edu[0]:
        st.markdown(
            f'<div style="background:#1e3a5f;border:1px solid #1e40af;padding:16px;border-radius:8px;text-align:center;">'
            f'<div style="color:#93c5fd;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Detected Level</div>'
            f'<div style="color:#f1f5f9;font-size:20px;font-weight:700;margin-top:6px;">{html_lib.escape(str(grade_level))}</div>'
            f'<div style="color:#64748b;font-size:13px;margin-top:4px;">{html_lib.escape(str(edu.get("current_level","") ))}</div>'
            f'</div>', unsafe_allow_html=True)
        if edu.get("recommended_stream"):
            st.markdown("")
            st.markdown(
                f'<div style="background:#172554;border:1px solid #1e40af;padding:12px;border-radius:8px;">'
                f'<div style="color:#93c5fd;font-size:11px;font-weight:700;text-transform:uppercase;">Recommended Stream</div>'
                f'<div style="color:#f1f5f9;font-size:14px;margin-top:4px;">{html_lib.escape(str(edu.get("recommended_stream","") ))}</div>'
                f'</div>', unsafe_allow_html=True)
        if edu.get("timeline"):
            st.markdown("")
            st.markdown(
                f'<div style="background:#0f2417;border:1px solid #166534;padding:12px;border-radius:8px;">'
                f'<div style="color:#86efac;font-size:11px;font-weight:700;text-transform:uppercase;">Timeline</div>'
                f'<div style="color:#f1f5f9;font-size:13px;margin-top:4px;">{html_lib.escape(str(edu.get("timeline","") ))}</div>'
                f'</div>', unsafe_allow_html=True)

    with cols_edu[1]:
        next_steps = edu.get("next_steps", [])
        if next_steps:
            st.markdown("**Your path forward:**")
            for i, step in enumerate(next_steps, 1):
                st.markdown(
                    f'<div style="background:#1e293b;border-left:3px solid #6366f1;padding:10px 14px;'
                    f'border-radius:0 6px 6px 0;margin-bottom:8px;">'
                    f'<span style="color:#818cf8;font-weight:700;font-size:12px;">STEP {i}</span><br>'
                    f'<span style="color:#e2e8f0;font-size:14px;">{html_lib.escape(str(step))}</span>'
                    f'</div>', unsafe_allow_html=True)
    st.divider()

# ── Overall advice ────────────────────────────────────────────────
overall_advice = career_result.get("overall_advice","")
top_career     = career_result.get("top_career","")
if overall_advice:
    st.markdown(
        f'<div style="background:#1e293b;border-left:5px solid #6366f1;padding:16px 20px;border-radius:8px;">'
        f'<div style="color:#818cf8;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Best Match: {html_lib.escape(top_career)}</div>'
        f'<div style="color:#e2e8f0;font-size:15px;line-height:1.6;font-style:italic;">{html_lib.escape(overall_advice)}</div>'
        f'</div>', unsafe_allow_html=True)
    st.divider()

# ── Career recommendations ────────────────────────────────────────
careers = career_result.get("career_recommendations", [])
if careers:
    st.markdown("## 🏆 Your Top Career Matches")
    st.caption("Ranked by how well they match your academic profile.")

    for i, career in enumerate(careers):
        score  = career.get("match_score", 0)
        title  = career.get("title", "")
        field  = career.get("field", "")
        bar_color = "#22c55e" if score>=80 else ("#f59e0b" if score>=60 else "#ef4444")
        rank_icon = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"

        # Full header card — all safe values
        st.markdown(
            f'<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;'
            f'padding:16px 20px 12px 20px;margin-top:20px;">'
            f'<div style="display:flex;align-items:flex-start;gap:12px;">'
            f'<span style="font-size:24px;line-height:1;">{rank_icon}</span>'
            f'<div style="flex:1;">'
            f'<div style="color:#f1f5f9;font-size:18px;font-weight:700;">{html_lib.escape(title)}</div>'
            f'<div style="color:#94a3b8;font-size:13px;margin-bottom:8px;">{html_lib.escape(field)}</div>'
            f'<div style="background:#334155;border-radius:4px;height:6px;">'
            f'<div style="background:{bar_color};width:{score}%;height:6px;border-radius:4px;"></div>'
            f'</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="color:#94a3b8;font-size:11px;">Match Score</div>'
            f'<div style="color:{bar_color};font-size:24px;font-weight:700;">{score}%</div>'
            f'</div>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

        # Card body using native Streamlit — no GPT text in HTML
        with st.container():
            inner_c1, inner_c2 = st.columns(2)
            with inner_c1:
                st.markdown(f"**Why this suits you:** {career.get('match_reasoning','')}")

                req = career.get("required_subjects_now", career.get("required_subjects", []))
                if req:
                    st.markdown("**📚 Subjects to strengthen now:**")
                    for s in req: st.markdown(f"  - {s}")

                degrees = career.get("degree_options", [])
                if degrees:
                    st.markdown("**🎓 Degree options:**")
                    for d in degrees: st.markdown(f"  - {d}")

            with inner_c2:
                gaps = career.get("skill_gaps", [])
                if gaps:
                    st.markdown("**⚠️ Skill gaps to close:**")
                    for g in gaps: st.markdown(f"  - {g}")

                roles = career.get("job_roles", [])
                if roles:
                    st.markdown("**💼 Job roles:**")
                    for r in roles: st.markdown(f"  - {r}")

                salary = career.get("salary_range_pkr", career.get("salary_range",""))
                if salary:
                    st.markdown(f"**💰 Salary range:** {salary}")

            resources = career.get("resources", [])
            if resources:
                st.markdown("**🔗 Learning resources:**")
                res_cols = st.columns(min(len(resources), 3))
                for ri, resource in enumerate(resources):
                    with res_cols[ri % len(res_cols)]:
                        r_name = resource.get("name","")
                        r_type = resource.get("type","")
                        r_url  = resource.get("url","")
                        st.markdown(
                            f'<div style="background:#0f172a;border:1px solid #334155;'
                            f'padding:10px 12px;border-radius:6px;margin-bottom:6px;">'
                            f'<div style="color:#e2e8f0;font-size:13px;font-weight:600;">{html_lib.escape(r_name)}</div>'
                            f'<div style="color:#64748b;font-size:11px;">{html_lib.escape(r_type)}</div>'
                            f'</div>', unsafe_allow_html=True)
                        if r_url and r_url.startswith("http"):
                            st.markdown(f"[Open →]({r_url})")
                        elif r_url:
                            st.caption(r_url)

        st.markdown('<hr style="border-color:#1e293b;margin:4px 0;">', unsafe_allow_html=True)

st.divider()

# ── 8-Week Roadmap ────────────────────────────────────────────────
roadmap = career_result.get("roadmap", {})
if roadmap:
    st.markdown(f"## 📅 8-Week Study Roadmap")
    st.markdown(f"**Career:** {roadmap.get('career', top_career)}")
    goal = roadmap.get("goal","")
    if goal:
        st.markdown(
            f'<div style="background:#0f172a;border:1px solid #1e40af;padding:12px 16px;'
            f'border-radius:8px;margin-bottom:16px;">'
            f'<span style="color:#93c5fd;font-weight:700;">🎯 Goal: </span>'
            f'<span style="color:#e2e8f0;">{html_lib.escape(goal)}</span>'
            f'</div>', unsafe_allow_html=True)

    weeks = roadmap.get("weeks", [])
    for row_start in range(0, len(weeks), 2):
        row_weeks = weeks[row_start:row_start+2]
        cols = st.columns(len(row_weeks))
        for col, wd in zip(cols, row_weeks):
            with col:
                week_num  = wd.get("week","")
                theme     = html_lib.escape(str(wd.get("theme","")))
                focus     = wd.get("focus_subjects",[])
                tasks     = wd.get("tasks",[])
                milestone = html_lib.escape(str(wd.get("milestone","")))

                tasks_html = "".join(
                    f'<div style="color:#cbd5e1;font-size:13px;margin:3px 0;">✓ {html_lib.escape(str(t))}</div>'
                    for t in tasks)
                focus_html = " · ".join(f'<strong style="color:#93c5fd;">{html_lib.escape(str(s))}</strong>' for s in focus)

                st.markdown(
                    f'<div style="background:#0f172a;border:1px solid #1e40af;border-radius:8px;'
                    f'margin-bottom:12px;overflow:hidden;">'
                    f'<div style="background:#1e3a5f;padding:10px 14px;">'
                    f'<span style="color:#93c5fd;font-size:11px;font-weight:700;">WEEK {week_num}</span>'
                    f'<div style="color:#f1f5f9;font-size:14px;font-weight:700;">{theme}</div>'
                    f'</div>'
                    f'<div style="padding:12px 14px;">'
                    f'<div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Focus</div>'
                    f'<div style="margin-bottom:10px;">{focus_html}</div>'
                    f'<div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Tasks</div>'
                    f'{tasks_html}'
                    f'<div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;margin:10px 0 4px;">Milestone</div>'
                    f'<div style="color:#86efac;font-size:13px;font-style:italic;">🏁 {milestone}</div>'
                    f'</div>'
                    f'</div>', unsafe_allow_html=True)

st.divider()

# ── Immediate actions ─────────────────────────────────────────────
immediate = career_result.get("immediate_actions", [])
if immediate:
    st.markdown("## ⚡ Take Action This Week")
    st.caption("3 things you can do right now to start moving towards your goal.")
    action_cols = st.columns(3)
    icons = ["1️⃣","2️⃣","3️⃣"]
    for i, action in enumerate(immediate[:3]):
        with action_cols[i]:
            st.markdown(
                f'<div style="background:#1e293b;border:1px solid #334155;padding:16px;'
                f'border-radius:8px;min-height:90px;">'
                f'<div style="font-size:20px;margin-bottom:8px;">{icons[i]}</div>'
                f'<div style="color:#e2e8f0;font-size:14px;line-height:1.5;">{html_lib.escape(str(action))}</div>'
                f'</div>', unsafe_allow_html=True)

st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("🤖 Start AI Tutoring", use_container_width=True, type="primary"):
        st.switch_page("pages/4_Tutor_Chat.py")
with c2:
    if st.button("📊 Back to Analysis", use_container_width=True):
        st.switch_page("pages/3_Analysis.py")
