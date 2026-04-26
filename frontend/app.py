"""App entry: defines navigation, injects theme, renders persistent sidebar."""
import streamlit as st

st.set_page_config(
    page_title="ContentForge-AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui import inject_theme, render_sidebar  # noqa: E402  (must run after set_page_config)

inject_theme()

# IMPORTANT: register pages with st.navigation BEFORE rendering the sidebar.
# The sidebar contains buttons that call st.switch_page; if navigation hasn't
# registered the page paths yet, switch_page raises.
pages = [
    st.Page("pages/1_Idea_Input.py", title="Idea Input", icon="✨", default=True),
    st.Page("pages/2_Agent_Pipeline.py", title="Agent Pipeline", icon="⚙️"),
    st.Page("pages/3_Final_Output.py", title="Final Output", icon="📄"),
    st.Page("pages/4_Trends_Dashboard.py", title="Trends Dashboard", icon="📊"),
]
pg = st.navigation(pages, position="hidden")

render_sidebar()

pg.run()
