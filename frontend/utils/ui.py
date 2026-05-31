"""
Shared Streamlit UI — modern app shell, navigation, and components.
"""

from __future__ import annotations

import html as html_lib
from typing import Any

import streamlit as st

# nav_id, label, path, accent color
NAV_ITEMS = [
    ("home", "Home", "app.py", "#6366f1"),
    ("login", "Login", "pages/1_Login.py", "#94a3b8"),
    ("upload", "Upload", "pages/2_Upload_Marksheet.py", "#3b82f6"),
    ("analysis", "Analysis", "pages/3_Analysis.py", "#8b5cf6"),
    ("tutor", "AI Tutor", "pages/4_Tutor_Chat.py", "#06b6d4"),
    ("career", "Career", "pages/5_Career_Roadmap.py", "#f59e0b"),
    ("quizzes", "Quizzes", "pages/6_Quizzes.py", "#ec4899"),
    ("dashboard", "Dashboard", "pages/7_Dashboard.py", "#10b981"),
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(15,23,42,0)",
    plot_bgcolor="rgba(15,23,42,0)",
    font=dict(family="Inter, sans-serif", color="#e2e8f0", size=12),
    margin=dict(t=24, b=48, l=24, r=24),
    xaxis=dict(gridcolor="rgba(51,65,85,0.5)", zeroline=False),
    yaxis=dict(gridcolor="rgba(51,65,85,0.5)", zeroline=False),
    legend=dict(bgcolor="rgba(30,41,59,0.8)", bordercolor="#334155", borderwidth=1),
)


def esc(text: Any) -> str:
    return html_lib.escape(str(text))


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #070b14;
    --surface: #111827;
    --surface-2: #1a2234;
    --border: rgba(148, 163, 184, 0.14);
    --text: #f8fafc;
    --muted: #94a3b8;
    --accent: #6366f1;
    --accent-2: #8b5cf6;
    --glow: rgba(99, 102, 241, 0.45);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif !important;
}

.stApp {
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(99,102,241,0.18), transparent 50%),
        radial-gradient(ellipse 60% 40% at 90% 10%, rgba(139,92,246,0.12), transparent 45%),
        radial-gradient(ellipse 50% 30% at 50% 100%, rgba(6,182,212,0.08), transparent 50%),
        var(--bg) !important;
}

#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

.block-container {
    padding: 1.25rem 2rem 2.5rem 2rem;
    max-width: 1280px;
}

section[data-testid="stSidebar"] {
    background: rgba(11, 17, 32, 0.92) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
    transition: all 0.2s ease !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 28px rgba(99, 102, 241, 0.5) !important;
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.6) !important;
    color: #e2e8f0 !important;
}

.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    border-radius: 12px !important;
    border-color: var(--border) !important;
    background: rgba(15, 23, 42, 0.8) !important;
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}

div[data-testid="stMetric"] label {
    color: var(--muted) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(15, 23, 42, 0.8);
    padding: 5px;
    border-radius: 14px;
    border: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
    border-radius: 10px !important;
}

.stFileUploader section[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed rgba(99, 102, 241, 0.4) !important;
    border-radius: 16px !important;
    background: rgba(15, 23, 42, 0.5) !important;
}

.stFileUploader section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #6366f1 !important;
    background: rgba(99, 102, 241, 0.06) !important;
}

[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    border: 1px solid var(--border) !important;
    background: rgba(30, 41, 59, 0.5) !important;
}

.stChatInputContainer {
    border-radius: 16px !important;
    border: 1px solid var(--border) !important;
}

/* ── Components ── */

.ui-mesh-bg {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: -1;
    opacity: 0.6;
}

.ui-glass {
    background: linear-gradient(145deg, rgba(30,41,59,0.55), rgba(15,23,42,0.75));
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}

.ui-hero-pro {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(124,58,237,0.15) 50%, rgba(15,23,42,0.9) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 24px;
    padding: 2.25rem 2.5rem;
    margin-bottom: 1.75rem;
}

.ui-hero-pro::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
    pointer-events: none;
}

.ui-hero-pro .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 6px 12px;
    border-radius: 100px;
    margin-bottom: 1rem;
}

.ui-hero-pro h1 {
    color: #fff;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0 0 0.6rem 0;
    line-height: 1.15;
}

.ui-hero-pro p {
    color: #cbd5e1;
    font-size: 1.05rem;
    margin: 0;
    max-width: 560px;
    line-height: 1.6;
}

.ui-page-head {
    margin-bottom: 1.5rem;
}

.ui-page-head h1 {
    color: #fff;
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
}

.ui-page-head p {
    color: var(--muted);
    font-size: 0.95rem;
    margin: 0.4rem 0 0 0;
}

.ui-stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}

@media (max-width: 900px) {
    .ui-stat-grid { grid-template-columns: repeat(2, 1fr); }
}

.ui-stat {
    background: linear-gradient(160deg, rgba(30,41,59,0.8), rgba(15,23,42,0.95));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    position: relative;
    overflow: hidden;
}

.ui-stat::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent-bar, #6366f1);
}

.ui-stat .label {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.ui-stat .value {
    color: #fff;
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 0.35rem;
    letter-spacing: -0.02em;
}

.ui-stat .hint {
    color: #64748b;
    font-size: 0.78rem;
    margin-top: 0.25rem;
}

.ui-tile {
    background: linear-gradient(160deg, rgba(30,41,59,0.65), rgba(15,23,42,0.9));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.35rem;
    height: 100%;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.ui-tile:hover {
    border-color: rgba(99, 102, 241, 0.45);
    box-shadow: 0 12px 40px rgba(99, 102, 241, 0.12);
    transform: translateY(-2px);
}

.ui-tile .icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 1rem;
}

.ui-tile h3 {
    color: #fff;
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0 0 0.4rem 0;
}

.ui-tile p {
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.55;
    margin: 0;
    flex: 1;
}

.ui-tile .arrow {
    color: #818cf8;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
}

.ui-sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.25rem 0.5rem 1.25rem 0.5rem;
}

.ui-sidebar-logo .mark {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    box-shadow: 0 4px 16px rgba(99,102,241,0.4);
}

.ui-sidebar-logo .text .name {
    color: #fff;
    font-weight: 800;
    font-size: 0.95rem;
    letter-spacing: -0.02em;
}

.ui-sidebar-logo .text .sub {
    color: #64748b;
    font-size: 0.68rem;
    font-weight: 500;
}

.ui-user-pill {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 10px 12px;
    margin-bottom: 1rem;
}

.ui-user-pill .avatar {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 0.85rem;
}

.ui-user-pill .info .name {
    color: #f1f5f9;
    font-weight: 700;
    font-size: 0.85rem;
}

.ui-user-pill .info .role {
    color: #818cf8;
    font-size: 0.7rem;
    font-weight: 600;
}

.ui-nav-section {
    color: #64748b;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.5rem 0.75rem 0.35rem;
    margin-top: 0.25rem;
}

.ui-login-split-left {
    background: linear-gradient(160deg, rgba(99,102,241,0.15) 0%, rgba(15,23,42,0.95) 60%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2.5rem 2rem;
    min-height: 520px;
}

.ui-login-split-left h1 {
    color: #fff;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 1rem 0 0.75rem 0;
}

.ui-login-split-left .lead {
    color: #94a3b8;
    line-height: 1.65;
    font-size: 0.95rem;
}

.ui-feature-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-top: 1.25rem;
    padding: 12px;
    background: rgba(15,23,42,0.5);
    border-radius: 12px;
    border: 1px solid var(--border);
}

.ui-feature-row .fi {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.ui-feature-row strong {
    color: #f1f5f9;
    font-size: 0.88rem;
}

.ui-feature-row span {
    color: #64748b;
    font-size: 0.78rem;
    display: block;
    margin-top: 2px;
}

.ui-form-card {
    background: linear-gradient(160deg, rgba(30,41,59,0.7), rgba(15,23,42,0.95));
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2rem 1.75rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
}

.ui-form-card h2 {
    color: #fff;
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0 0 0.25rem 0;
}

.ui-form-card .sub {
    color: #64748b;
    font-size: 0.88rem;
    margin-bottom: 1.25rem;
}

.ui-step {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.3);
    color: #a5b4fc;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 100px;
    margin-bottom: 0.75rem;
}

.ui-empty {
    text-align: center;
    padding: 3rem 2rem;
    background: rgba(15,23,42,0.5);
    border: 1px dashed var(--border);
    border-radius: 20px;
}

.ui-empty .icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.ui-empty h3 { color: #f1f5f9; margin: 0 0 0.5rem 0; font-weight: 700; }
.ui-empty p { color: #64748b; margin: 0; font-size: 0.9rem; }

.ui-offline {
    background: rgba(127, 29, 29, 0.3);
    border: 1px solid #b91c1c;
    border-radius: 16px;
    padding: 1.25rem;
    color: #fecaca;
}

.ui-section-label {
    color: #64748b;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 1.5rem 0 0.75rem 0;
}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def apply_plotly_theme(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def check_backend(client) -> None:
    if not client.health_check():
        inject_theme()
        st.markdown(
            '<div class="ui-offline"><strong>Backend offline</strong><br>'
            "Start FastAPI, then refresh.</div>",
            unsafe_allow_html=True,
        )
        st.code("uvicorn backend.main:app --reload --port 8000", language="bash")
        st.stop()


def require_login() -> None:
    if not st.session_state.get("logged_in"):
        inject_theme()
        empty_state(
            "🔒",
            "Sign in required",
            "Log in to access this page.",
            "Go to Login",
            "pages/1_Login.py",
        )
        st.stop()


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="ui-page-head"><h1>{esc(title)}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def hero_pro(title: str, subtitle: str, eyebrow: str = "AI-Powered Learning") -> None:
    st.markdown(
        f'<div class="ui-hero-pro">'
        f'<div class="eyebrow">✦ {esc(eyebrow)}</div>'
        f"<h1>{esc(title)}</h1>"
        f"<p>{esc(subtitle)}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def stat_row(stats: list[tuple[str, str, str, str]]) -> None:
    """stats: [(value, label, hint, accent_color), ...]"""
    cards = []
    for value, label, hint, accent in stats[:4]:
        cards.append(
            f'<div class="ui-stat" style="--accent-bar:{accent};">'
            f'<div class="label">{esc(label)}</div>'
            f'<div class="value">{esc(value)}</div>'
            f'<div class="hint">{esc(hint)}</div></div>'
        )
    while len(cards) < 4:
        cards.append(
            '<div class="ui-stat" style="--accent-bar:#334155;">'
            '<div class="label">—</div><div class="value">—</div>'
            '<div class="hint">No data yet</div></div>'
        )
    st.markdown(
        f'<div class="ui-stat-grid">{"".join(cards[:4])}</div>',
        unsafe_allow_html=True,
    )


def action_tile(icon: str, icon_bg: str, title: str, desc: str) -> None:
    st.markdown(
        f'<div class="ui-tile">'
        f'<div class="icon-wrap" style="background:{icon_bg};">{icon}</div>'
        f"<h3>{esc(title)}</h3>"
        f"<p>{esc(desc)}</p>"
        f'<div class="arrow">Open →</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, message: str, cta: str, page: str) -> None:
    st.markdown(
        f'<div class="ui-empty">'
        f'<div class="icon">{icon}</div>'
        f"<h3>{esc(title)}</h3>"
        f"<p>{esc(message)}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if st.button(cta, type="primary"):
        st.switch_page(page)


def render_sidebar(current: str | None = None) -> None:
    inject_theme()
    with st.sidebar:
        st.markdown(
            '<div class="ui-sidebar-logo">'
            '<div class="mark">🎓</div>'
            '<div class="text"><div class="name">AI Tutor</div>'
            '<div class="sub">Agentic learning platform</div></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("logged_in"):
            name = st.session_state.get("full_name") or st.session_state.get("username", "U")
            role = (st.session_state.get("role") or "student").capitalize()
            initial = esc(name[0].upper())
            st.markdown(
                f'<div class="ui-user-pill">'
                f'<div class="avatar">{initial}</div>'
                f'<div class="info"><div class="name">{esc(name)}</div>'
                f'<div class="role">{esc(role)}</div></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="ui-nav-section">Navigation</div>', unsafe_allow_html=True)

        for nav_id, label, path, _accent in NAV_ITEMS:
            if nav_id == "login" and st.session_state.get("logged_in"):
                continue
            btn_type = "primary" if nav_id == current else "secondary"
            if st.button(label, key=f"nav_{nav_id}", use_container_width=True, type=btn_type):
                if nav_id != current:
                    st.switch_page(path)

        st.divider()
        if st.session_state.get("logged_in"):
            if st.button("Sign out", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


def render_landing() -> None:
    inject_theme()
    hero_pro(
        "Learn smarter with your AI tutor",
        "Upload marksheets, get instant analysis, personalised tutoring, career roadmaps, "
        "and adaptive quizzes — built for students.",
        "Agentic AI Tutor",
    )

    c1, c2, c3 = st.columns(3)
    tiles = [
        ("📄", "rgba(59,130,246,0.2)", "Marksheet OCR", "Extract grades from photos or PDFs in seconds."),
        ("🤖", "rgba(6,182,212,0.2)", "AI Tutor", "Adaptive chat sessions on your weakest subjects."),
        ("🎯", "rgba(236,72,153,0.2)", "Smart Quizzes", "MCQs generated to match your performance level."),
    ]
    for col, (icon, bg, title, desc) in zip([c1, c2, c3], tiles):
        with col:
            action_tile(icon, bg, title, desc)

    st.markdown("")
    b1, b2, _ = st.columns([2, 2, 3])
    with b1:
        if st.button("Get started — Sign in", type="primary", use_container_width=True):
            st.switch_page("pages/1_Login.py")
    with b2:
        if st.button("Create free account", use_container_width=True):
            st.switch_page("pages/1_Login.py")


def render_login_split() -> None:
    """Left branding column HTML (use inside st.columns)."""
    return """
    <div class="ui-login-split-left">
        <div class="eyebrow" style="display:inline-flex;align-items:center;gap:6px;
            background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.35);
            color:#a5b4fc;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
            text-transform:uppercase;padding:6px 12px;border-radius:100px;">
            ✦ Agentic AI Tutor
        </div>
        <h1>Your personal<br>learning cockpit</h1>
        <p class="lead">Everything you need to understand your grades, improve weak areas,
        and plan your future — powered by GPT-4o agents.</p>
        <div class="ui-feature-row">
            <div class="fi" style="background:rgba(99,102,241,0.2);">📊</div>
            <div><strong>Deep grade analysis</strong><span>Patterns, priorities, study tips</span></div>
        </div>
        <div class="ui-feature-row">
            <div class="fi" style="background:rgba(6,182,212,0.2);">🤖</div>
            <div><strong>LangGraph AI tutor</strong><span>Interactive sessions per subject</span></div>
        </div>
        <div class="ui-feature-row">
            <div class="fi" style="background:rgba(245,158,11,0.2);">🧭</div>
            <div><strong>Career roadmap</strong><span>8-week plans matched to your profile</span></div>
        </div>
    </div>
    """


def step_badge(text: str) -> None:
    st.markdown(f'<div class="ui-step">Step {esc(text)}</div>', unsafe_allow_html=True)
