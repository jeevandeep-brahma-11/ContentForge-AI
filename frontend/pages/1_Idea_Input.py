import streamlit as st

from ui import inject_theme, render_banner, render_breadcrumb
from utils import api_post

inject_theme()
render_banner(
    "Spark a new video",
    "Drop a topic — six agents research, write, validate, and package it into a script.",
)
render_breadcrumb("idea")

with st.form("idea_form"):
    idea = st.text_area(
        "Video idea / topic",
        placeholder="e.g. Why junior engineers should learn Rust in 2026",
        height=130,
    )
    col1, col2, col3 = st.columns(3)
    niche = col1.text_input("Niche / category", value="", placeholder="programming")
    target_length = col2.number_input("Length (minutes)", min_value=1, max_value=60, value=8)
    tone = col3.text_input("Tone", value="engaging, conversational")
    submitted = st.form_submit_button("✨  Submit to pipeline", type="primary", use_container_width=True)

if submitted:
    if not idea.strip():
        st.error("Idea cannot be empty.")
    else:
        try:
            resp = api_post(
                "/idea/submit",
                {
                    "idea": idea,
                    "niche": niche,
                    "target_length_minutes": int(target_length),
                    "tone": tone,
                },
            )
            st.session_state["last_run_id"] = resp["run_id"]
            st.success("Pipeline started.")
            st.info("Track progress on the **Agent Pipeline** step.", icon="👉")
            if st.button("Go to Agent Pipeline →", type="primary"):
                st.switch_page("pages/2_Agent_Pipeline.py")
        except Exception as exc:
            st.error(f"Failed to submit: {exc}")
