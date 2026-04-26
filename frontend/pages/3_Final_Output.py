import json

import streamlit as st

from ui import inject_theme, render_banner, render_breadcrumb
from utils import api_get, api_post, fmt_ist_time

inject_theme()
render_banner(
    "Final output",
    "Review, approve, and download the video + voiceover scripts — ready for your tools of choice.",
)
render_breadcrumb("final")

runs = api_get("/agents/status").get("runs", [])
approvable = [r for r in runs if r["status"] == "awaiting_approval"]
if not approvable:
    st.info("No runs are awaiting approval yet.", icon="⏳")
    st.stop()

# Human-readable labels — no run_id shown.
labels = {
    f"{r['idea'][:70]}  ·  {fmt_ist_time(r['updated_at'])}": r["run_id"]
    for r in approvable
}
default = st.session_state.get("last_run_id")
default_label = next((k for k, v in labels.items() if v == default), None)
selected = st.selectbox(
    "Pick a run to review",
    list(labels.keys()),
    index=list(labels.keys()).index(default_label) if default_label else 0,
)
run_id = labels[selected]
status = api_get("/agents/status", {"run_id": run_id})
outputs = status["outputs"]

script = outputs.get("script_writer", {}) or {}
opt = outputs.get("optimization", {}) or {}
media = outputs.get("media_generation", {}) or {}
validation = outputs.get("validation", {}) or {}

st.markdown(f"### {opt.get('title', '(no title)')}")
score = validation.get("overall", "—")
st.caption(f"Validation score · **{score}**/10  ·  Updated {fmt_ist_time(status['updated_at'])} IST")

with st.expander("🎯 Hook", expanded=True):
    st.write(script.get("hook", ""))
with st.expander("📜 Full script"):
    st.write(script.get("script", ""))
with st.expander("📝 Description"):
    st.write(opt.get("description", ""))
with st.expander("🏷️ Tags"):
    st.write(", ".join(opt.get("tags", [])))
with st.expander("🖼️ Thumbnail ideas"):
    st.write("**Text options:**", opt.get("thumbnail_text_options", []))
    st.write("**Visual concepts:**", opt.get("thumbnail_visual_concepts", []))
with st.expander("🎬 Scenes"):
    for s in media.get("scenes", []):
        st.markdown(f"**Scene {s.get('index')}** · {s.get('duration_seconds')}s")
        st.code(s.get("visual_prompt", ""), language="text")
        st.caption(s.get("narration", ""))

st.divider()
st.subheader("Approve & export scripts")
st.caption("The agents already produced the scripts — approval just finalizes and unlocks downloads.")

if st.button("✓  Approve & export", type="primary", use_container_width=True):
    try:
        result = api_post("/generate/final", {"run_id": run_id})
        st.session_state[f"export_{run_id}"] = result
        st.success("Scripts ready — download below.", icon="🎉")
    except Exception as exc:
        st.error(f"Export failed: {exc}")

exports = st.session_state.get(f"export_{run_id}", {}).get("exports")
if exports:
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "⬇  voiceover.txt",
        data=exports["voiceover_txt"],
        file_name="voiceover.txt",
        mime="text/plain",
        use_container_width=True,
    )
    col2.download_button(
        "⬇  video_script.md",
        data=exports["video_script_md"],
        file_name="video_script.md",
        mime="text/markdown",
        use_container_width=True,
    )
    col3.download_button(
        "⬇  scenes.json",
        data=json.dumps(exports["scenes_json"], indent=2),
        file_name="scenes.json",
        mime="application/json",
        use_container_width=True,
    )
    with st.expander("👀 Preview video_script.md"):
        st.markdown(exports["video_script_md"])
