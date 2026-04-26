import streamlit as st

from ui import inject_theme, render_banner
from utils import api_get, api_post, fmt_ist_datetime

inject_theme()
render_banner(
    "Trends dashboard",
    "What American YouTube viewers are watching in your niches — sorted by trendiness.",
)

col1, col2, col3 = st.columns([1, 1.2, 4])
with col1:
    if st.button("← Back", use_container_width=True):
        st.switch_page("pages/1_Idea_Input.py")
with col2:
    refresh_clicked = st.button("↻  Refresh", use_container_width=True, type="primary")
with col3:
    scan_now = st.button("⚡  Run trend scan now", use_container_width=True)

if scan_now:
    with st.spinner("Scanning trends (1 Firecrawl call per niche)…"):
        try:
            api_post("/trends/refresh", {})
            st.session_state.pop("trends_cache", None)
            st.success("Scan complete.")
        except Exception as exc:
            st.error(f"Scan failed: {exc}")

# Fetch only on first load or explicit refresh.
if "trends_cache" not in st.session_state or refresh_clicked or scan_now:
    with st.spinner("Fetching latest snapshots…"):
        try:
            st.session_state["trends_cache"] = api_get("/trends")
        except Exception as exc:
            st.error(f"Failed to fetch trends: {exc}")
            st.stop()

data = st.session_state.get("trends_cache", {})
snapshots = data.get("snapshots", [])
if not snapshots:
    st.info(
        "No trend snapshots yet. Click **Run trend scan now**, or wait for the "
        "background worker (default: every 60 min).",
        icon="⏳",
    )
    st.stop()

niches = sorted({s["niche"] for s in snapshots})
niche_filter = st.multiselect("Filter by niche", niches, default=niches)

for snap in snapshots:
    if snap["niche"] not in niche_filter:
        continue
    payload = snap["payload"]
    items = payload.get("items", []) if isinstance(payload, dict) else []
    header = f"**{snap['niche']}**  ·  {fmt_ist_datetime(snap['created_at'])}"
    with st.expander(header, expanded=True):
        if not items:
            st.caption("No structured items in this snapshot.")
            continue
        items_sorted = sorted(items, key=lambda x: x.get("trend_score", 0), reverse=True)
        display_rows = [
            {
                "#": i.get("rank", n + 1),
                "Topic": i.get("topic", ""),
                "Genre": i.get("genre", ""),
                "Length (min)": i.get("typical_length_min", "—"),
                "Trend": i.get("trend_score", "—"),
                "US viewership": i.get("us_viewership", "—"),
                "Why trending": i.get("why_trending", ""),
            }
            for n, i in enumerate(items_sorted)
        ]
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
