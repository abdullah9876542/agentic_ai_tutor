"""
pages/2_Upload_Marksheet.py — Upload and process a marksheet
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient
from frontend.utils.ui import page_header, render_sidebar, require_login, step_badge

st.set_page_config(page_title="Upload Marksheet — AI Tutor", page_icon="📄", layout="wide")
require_login()
render_sidebar("upload")

client = APIClient()

page_header(
    "Upload Marksheet",
    "Upload a photo or scan of your result card. The AI will extract subject scores automatically.",
)
st.divider()

# ── Upload section ────────────────────────────────────────────────
col_upload, col_preview = st.columns([1, 1])

with col_upload:
    step_badge("1")
    st.markdown("#### Choose your file")
    uploaded_file = st.file_uploader(
        label="Drag and drop or browse",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        help="Supported formats: JPG, PNG, WEBP, PDF. Max 10 MB.",
    )

    if uploaded_file:
        st.success(f"✅ File selected: **{uploaded_file.name}** ({round(uploaded_file.size/1024, 1)} KB)")

with col_preview:
    if uploaded_file and uploaded_file.type.startswith("image"):
        st.markdown("#### Preview")
        st.image(uploaded_file, use_container_width=True)
    elif uploaded_file and uploaded_file.type == "application/pdf":
        st.markdown("#### Preview")
        st.info("📄 PDF selected. The first page will be processed.")

st.divider()

# ── Process button ────────────────────────────────────────────────
if uploaded_file:
    step_badge("2")
    st.markdown("#### Extract grades")
    st.caption(
        "The AI Agent will read your marksheet and extract every subject and score. "
        "This usually takes 10–20 seconds."
    )

    if st.button("Extract Grades from Marksheet", type="primary", use_container_width=True):
        with st.spinner("Sending to AI Vision Agent... please wait."):
            file_bytes = uploaded_file.read()
            res = client.upload_marksheet(
                user_id    = st.session_state.user_id,
                file_bytes = file_bytes,
                filename   = uploaded_file.name,
            )

        if res["success"]:
            data = res["data"]
            st.success(data["message"])

            # Save marksheet_id to session for use in Analysis page
            st.session_state.marksheet_id  = data["marksheet_id"]
            st.session_state.latest_grades = data["grades"]

            st.divider()
            st.markdown("### ✅ Extracted Grades")

            if data.get("raw_text"):
                st.info(f"📝 **Summary:** {data['raw_text']}")

            # Show grades table
            grades = data["grades"]
            if grades:
                df = pd.DataFrame(grades)

                # Add percentage column if score and max_score are available
                def calc_percent(row):
                    try:
                        if row["score"] is not None and row["max_score"]:
                            return round((row["score"] / row["max_score"]) * 100, 1)
                    except Exception:
                        pass
                    return None

                df["percentage"] = df.apply(calc_percent, axis=1)
                df = df.rename(columns={
                    "subject":   "Subject",
                    "score":     "Score",
                    "max_score": "Max Score",
                    "grade":     "Grade",
                    "percentage": "Percentage %",
                })

                st.dataframe(df, use_container_width=True, hide_index=True)

                # Quick summary stats
                valid_pct = df["Percentage %"].dropna()
                if not valid_pct.empty:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📚 Subjects Found", len(grades))
                    m2.metric("📈 Highest Score", f"{valid_pct.max()}%")
                    m3.metric("📉 Lowest Score",  f"{valid_pct.min()}%")

            st.divider()
            st.markdown("#### What's next?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📊 View Full Analysis", use_container_width=True, type="primary"):
                    st.switch_page("pages/3_Analysis.py")
            with c2:
                if st.button("🏠 Back to Home", use_container_width=True):
                    st.switch_page("app.py")

        else:
            st.error(f"❌ {res['error']}")
            st.caption("Tips: Make sure the image is clear and shows the full result card.")

else:
    st.info("👆 Upload a marksheet file above to get started.")

# ── Previous uploads ──────────────────────────────────────────────
st.divider()
with st.expander("📂 View previous uploads"):
    prev = client.get_marksheets(st.session_state.user_id)
    if prev["success"]:
        marksheets = prev["data"].get("marksheets", [])
        if marksheets:
            for ms in marksheets:
                with st.container():
                    st.markdown(f"**Marksheet #{ms['id']}** — Uploaded: {ms['uploaded_at'][:10]}")
                    if ms.get("grades"):
                        mini_df = pd.DataFrame(ms["grades"])
                        mini_df = mini_df.rename(columns={
                            "subject": "Subject", "score": "Score",
                            "max_score": "Max", "grade": "Grade"
                        })
                        st.dataframe(mini_df, use_container_width=True, hide_index=True)
                    st.divider()
        else:
            st.info("No previous uploads found.")
    else:
        st.warning(f"Could not load previous uploads: {prev['error']}")
