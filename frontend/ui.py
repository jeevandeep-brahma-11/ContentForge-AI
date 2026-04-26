"""Shared UI: theme, hero banner, breadcrumb, sidebar with compact chat-brick history."""
from __future__ import annotations

import streamlit as st

from utils import api_delete, api_get, fmt_ist_time

BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, .stApp, [data-testid="stSidebar"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0F172A;
}
h1, h2, h3, h4 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.02em !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}
p, div, span, label { color: #1F2937; }

/* --- App surface --- */
.stApp {
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(79, 70, 229, 0.06), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(219, 39, 119, 0.05), transparent 60%),
        #FAFAFA;
}
.block-container { padding-top: 2rem !important; max-width: 1180px; }

/* --- Hero banner --- */
.cf-banner {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 45%, #DB2777 100%);
    padding: 2rem 2.5rem;
    border-radius: 20px;
    margin: 0.25rem 0 1.75rem 0;
    box-shadow: 0 12px 32px rgba(79, 70, 229, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.18);
    position: relative;
    overflow: hidden;
}
.cf-banner::before {
    content: "";
    position: absolute; top: -40%; right: -15%;
    width: 420px; height: 420px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.16), transparent 70%);
    pointer-events: none;
}
.cf-banner h1 { color: #FFFFFF !important; margin: 0 !important; font-size: 2.25rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; position: relative; }
.cf-banner p { color: rgba(255, 255, 255, 0.92) !important; margin: 0.5rem 0 0 0 !important; font-size: 1.05rem; font-weight: 400; position: relative; }

/* --- Breadcrumb --- */
.cf-steps-wrap {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px;
    padding: 0.45rem; margin-bottom: 1.75rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.cf-home-prefix {
    display: inline-block; padding: 0.5rem 0.9rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700; font-size: 0.88rem; color: #4F46E5; letter-spacing: -0.01em;
}
.cf-sep { color: #CBD5E1; padding: 0 0.15rem; font-size: 1.05rem; line-height: 2.3rem; text-align: center; }
.cf-steps-wrap .stButton > button {
    background: transparent !important; color: #64748B !important;
    border: 1px solid transparent !important; font-weight: 500 !important;
    font-size: 0.88rem !important; padding: 0.45rem 1rem !important;
    transition: all 0.15s ease !important; border-radius: 9px !important; box-shadow: none !important;
}
.cf-steps-wrap .stButton > button:hover:not(:disabled) {
    background: #EEF2FF !important; color: #4338CA !important; border-color: #C7D2FE !important;
}
.cf-steps-wrap .stButton > button:disabled {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    color: #FFFFFF !important; opacity: 1 !important; font-weight: 600 !important;
}

/* --- Primary buttons (main area) --- */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    color: #FFFFFF !important; border: none !important; font-weight: 600 !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28) !important; transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.05); transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.38) !important;
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important; color: #1F2937 !important;
    border: 1px solid #E5E7EB !important; font-weight: 500 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #F9FAFB !important; border-color: #C7D2FE !important; color: #4338CA !important;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] { background: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { display: none; }

.cf-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.45rem; font-weight: 800;
    background: linear-gradient(135deg, #4F46E5, #DB2777);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    padding: 0.5rem 0 0.2rem 0; letter-spacing: -0.02em;
}
.cf-tagline {
    color: #64748B; font-size: 0.72rem; margin-bottom: 1.1rem;
    letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
}
.cf-side-label {
    color: #64748B; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
    margin: 1.4rem 0 0.5rem 0; text-transform: uppercase;
}

/* Sidebar top actions: New Idea + Trends — bold white on gradient */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    padding: 0.55rem 0.75rem !important; font-size: 0.88rem !important;
    text-align: center !important; justify-content: center !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
[data-testid="stSidebar"] .stButton > button[kind="primary"] div,
[data-testid="stSidebar"] .stButton > button[kind="primary"] span {
    color: #FFFFFF !important;
    font-weight: 800 !important;
}

/* --- Chat bricks (sidebar history) ------------------------------------
   Tight secondary buttons styled as compact chat list items.              */
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    color: #334155 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.38rem 0.55rem !important;
    margin-bottom: 0.22rem !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: all 0.12s ease !important;
    line-height: 1.25 !important;
    min-height: unset !important;
    height: 34px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] p,
[data-testid="stSidebar"] .stButton > button[kind="secondary"] div {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-size: 0.8rem !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: #EEF2FF !important;
    border-color: #C7D2FE !important;
    color: #4338CA !important;
}

/* The ✕ delete button — icon-only square */
[data-testid="stSidebar"] .stButton > button[kind="secondary"].cf-del {
    /* fallback — we target by column structure below */
}

/* Force tight columns gap in sidebar so brick + delete sit flush */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: 0.25rem !important;
}

/* --- Cards / expanders --- */
[data-testid="stExpander"] {
    background: #FFFFFF !important; border: 1px solid #E5E7EB !important;
    border-radius: 12px !important; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    margin-bottom: 0.5rem;
}
[data-testid="stExpander"] summary { font-weight: 600 !important; color: #0F172A !important; }

/* --- Metrics --- */
[data-testid="stMetric"] {
    background: #FFFFFF; padding: 1rem 1.25rem; border-radius: 14px;
    border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
[data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.7rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
[data-testid="stMetricValue"] { font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 700 !important; color: #0F172A !important; }

/* --- Inputs --- */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div {
    background: #FFFFFF !important; border: 1px solid #D1D5DB !important;
    border-radius: 10px !important; color: #0F172A !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #6366F1 !important; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label, .stSelectbox label {
    color: #374151 !important; font-weight: 500 !important;
}

/* --- Misc --- */
[data-testid="stAlert"] { border-radius: 12px !important; }
.stCodeBlock, pre {
    background: #F8FAFC !important; border: 1px solid #E5E7EB !important;
    border-radius: 10px !important; color: #0F172A !important;
}
hr { border-color: #E5E7EB !important; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
</style>
"""

STEPS = [
    ("idea", "Idea Input", "pages/1_Idea_Input.py"),
    ("pipeline", "Agent Pipeline", "pages/2_Agent_Pipeline.py"),
    ("final", "Final Output", "pages/3_Final_Output.py"),
]

STATUS_ICON = {
    "queued": "⏳",
    "running": "⚡",
    "awaiting_approval": "✓",
    "failed": "⚠",
}


def inject_theme() -> None:
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def render_banner(title: str, subtitle: str = "") -> None:
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="cf-banner"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def render_breadcrumb(current: str) -> None:
    st.markdown('<div class="cf-steps-wrap">', unsafe_allow_html=True)
    cols = st.columns([1.0, 0.15, 1.3, 0.15, 1.5, 0.15, 1.4, 4])
    with cols[0]:
        st.markdown('<div class="cf-home-prefix">◆ App</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="cf-sep">›</div>', unsafe_allow_html=True)
    for (key, label, path), btn_col, sep_col in zip(
        STEPS, [cols[2], cols[4], cols[6]], [cols[3], cols[5], None]
    ):
        with btn_col:
            is_current = key == current
            if st.button(label, key=f"cf_bc_{key}", use_container_width=True, disabled=is_current):
                st.switch_page(path)
        if sep_col is not None:
            with sep_col:
                st.markdown('<div class="cf-sep">›</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _idea_label(idea: str, word_count: int = 5) -> str:
    words = idea.strip().split()
    label = " ".join(words[:word_count])
    return label + ("…" if len(words) > word_count else "")


def render_sidebar() -> None:
    """Sidebar: brand, New Idea, Trends, compact DB-backed chat bricks with delete."""
    with st.sidebar:
        st.markdown('<div class="cf-brand">◆ ContentForge</div>', unsafe_allow_html=True)
        st.markdown('<div class="cf-tagline">Faceless YouTube · automated</div>', unsafe_allow_html=True)

        if st.button("➕  New Idea", key="cf_new_idea", use_container_width=True, type="primary"):
            st.session_state.pop("last_run_id", None)
            for k in list(st.session_state.keys()):
                if k.startswith("export_"):
                    del st.session_state[k]
            st.switch_page("pages/1_Idea_Input.py")

        if st.button("📊  Trends Dashboard", key="cf_trends_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Trends_Dashboard.py")

        st.markdown('<div class="cf-side-label">Chat History</div>', unsafe_allow_html=True)

        try:
            runs = api_get("/agents/status").get("runs", [])
        except Exception:
            st.caption("_Backend offline._")
            return

        if not runs:
            st.caption("_No runs yet — click New Idea._")
            return

        selected = st.session_state.get("last_run_id")
        for r in runs[:30]:
            icon = STATUS_ICON.get(r["status"], "•")
            idea_text = _idea_label(r["idea"])
            marker = "● " if r["run_id"] == selected else ""
            label = f"{marker}{icon}  {idea_text}"
            tooltip = (
                f"{r['idea']}\n"
                f"status: {r['status']}\n"
                f"updated: {fmt_ist_time(r['updated_at'])} IST"
            )

            c1, c2 = st.columns([6, 1])
            with c1:
                if st.button(label, key=f"cf_hist_{r['run_id']}", use_container_width=True, help=tooltip):
                    st.session_state["last_run_id"] = r["run_id"]
                    target = (
                        "pages/3_Final_Output.py"
                        if r["status"] == "awaiting_approval"
                        else "pages/2_Agent_Pipeline.py"
                    )
                    st.switch_page(target)
            with c2:
                if st.button("✕", key=f"cf_del_{r['run_id']}", use_container_width=True, help="Delete this chat"):
                    try:
                        api_delete(f"/agents/run/{r['run_id']}")
                        if st.session_state.get("last_run_id") == r["run_id"]:
                            st.session_state.pop("last_run_id", None)
                        st.session_state.pop(f"export_{r['run_id']}", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Delete failed: {exc}")
