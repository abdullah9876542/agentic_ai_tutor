"""
pages/1_Login.py — Login and Register
"""

import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.utils.ui import check_backend, inject_theme, render_login_split

st.set_page_config(page_title="Login — AI Tutor", page_icon="🔐", layout="wide")
inject_theme()

if st.session_state.get("logged_in"):
    st.success(f"Already logged in as **{st.session_state.username}**.")
    if st.button("Go to Home", type="primary"):
        st.switch_page("app.py")
    st.stop()

client = APIClient()
check_backend(client)

left, right = st.columns([1.05, 1], gap="large")

with left:
    st.markdown(render_login_split(), unsafe_allow_html=True)

with right:
    st.markdown(
        '<div class="ui-form-card">'
        "<h2>Welcome back</h2>"
        '<div class="sub">Sign in or create a new account</div></div>',
        unsafe_allow_html=True,
    )

    login_tab, reg_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your_username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            if not username.strip() or not password:
                st.warning("Please enter your username and password.")
            else:
                with st.spinner("Signing in..."):
                    res = client.login(username.strip(), password)
                if res["success"]:
                    u = res["data"]["user"]
                    st.session_state.logged_in = True
                    st.session_state.user_id = u["id"]
                    st.session_state.username = u["username"]
                    st.session_state.full_name = u.get("full_name") or u["username"]
                    st.session_state.role = u["role"]
                    st.session_state.email = u["email"]
                    st.success(res["data"]["message"])
                    st.balloons()
                    time.sleep(0.8)
                    st.switch_page("app.py")
                else:
                    st.error(res["error"])

    with reg_tab:
        with st.form("register_form"):
            c1, c2 = st.columns(2)
            with c1:
                r_username = st.text_input("Username *", placeholder="min. 3 chars")
            with c2:
                r_fullname = st.text_input("Full name", placeholder="Optional")

            r_email = st.text_input("Email *", placeholder="you@school.edu")

            c3, c4 = st.columns(2)
            with c3:
                r_password = st.text_input("Password *", type="password", placeholder="min. 6 chars")
            with c4:
                r_confirm = st.text_input("Confirm *", type="password")

            r_role = st.selectbox("I am a", ["student", "teacher"])
            reg_submitted = st.form_submit_button(
                "Create account", use_container_width=True, type="primary",
            )

        if reg_submitted:
            errors = []
            if not r_username.strip():
                errors.append("Username is required.")
            elif len(r_username.strip()) < 3:
                errors.append("Username must be at least 3 characters.")
            if not r_email.strip():
                errors.append("Email is required.")
            if not r_password:
                errors.append("Password is required.")
            elif len(r_password) < 6:
                errors.append("Password must be at least 6 characters.")
            elif r_password != r_confirm:
                errors.append("Passwords do not match.")

            for e in errors:
                st.warning(e)
            if not errors:
                with st.spinner("Creating account..."):
                    res = client.register(
                        username=r_username.strip(),
                        email=r_email.strip(),
                        password=r_password,
                        full_name=r_fullname.strip(),
                        role=r_role,
                    )
                if res["success"]:
                    st.success(res["data"]["message"])
                    st.info("Switch to **Sign in** to continue.")
                else:
                    st.error(res["error"])
