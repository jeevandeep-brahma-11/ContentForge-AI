import time

import streamlit as st

from ui import inject_theme, render_banner, render_breadcrumb
from utils import api_get, fmt_ist_time

inject_theme()
render_banner(
    "Agent pipeline",
    "Watch six agents run: research → ideation → script → validation → optimization → media.",
)
render_breadcrumb("pipeline")

all_runs = api_get("/agents/status").get("runs", [])
# Human-readable labels — no run_id shown.
run_options = {
    f"{r['idea'][:70]}  ·  {r['status']}  ·  {fmt_ist_time(r['updated_at'])}": r["run_id"]
    for r in all_runs
}
default = st.session_state.get("last_run_id")
default_label = next((k for k, v in run_options.items() if v == default), None)

if not run_options:
    st.info("No runs yet — click **New Idea** in the sidebar.", icon="💡")
    st.stop()

selected_label = st.selectbox(
    "Select run",
    list(run_options.keys()),
    index=list(run_options.keys()).index(default_label) if default_label else 0,
)
run_id = run_options[selected_label]
st.session_state["last_run_id"] = run_id

col_a, col_b, _ = st.columns([1.2, 1.2, 3])
auto_refresh = col_a.toggle("Auto-refresh (5s)", value=False)
if col_b.button("↻ Refresh now", use_container_width=True):
    st.rerun()

status = api_get("/agents/status", {"run_id": run_id})
agent_done = len(
    [
        k
        for k in status["outputs"]
        if k
        not in {
            "run_id", "idea", "niche", "target_length_minutes", "tone",
            "feedback_note", "loops", "max_loops", "revise_target", "logs",
        }
    ]
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Status", status["status"])
c2.metric("Current agent", status["current_agent"] or "—")
c3.metric("Agents done", f"{agent_done}/6")
c4.metric("Updated", fmt_ist_time(status["updated_at"]))

st.subheader("Logs")
logs = status.get("logs", [])
if logs:
    st.dataframe(logs, use_container_width=True, hide_index=True, height=220)
else:
    st.caption("No logs yet.")

st.subheader("Agent outputs")
for agent in ["research", "ideation", "script_writer", "validation", "optimization", "media_generation"]:
    data = status["outputs"].get(agent)
    if data:
        with st.expander(f"**{agent}**"):
            st.json(data, expanded=False)

if status["status"] == "awaiting_approval":
    st.success("Pipeline complete — head to **Final Output** to export scripts.", icon="✅")
    if st.button("Go to Final Output →", type="primary"):
        st.switch_page("pages/3_Final_Output.py")

if auto_refresh and status["status"] in {"queued", "running"}:
    time.sleep(5)
    st.rerun()
