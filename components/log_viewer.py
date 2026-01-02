import streamlit as st
import json
import os

LOG_FILE = "simulation_log.json"

def render_logs():
    st.subheader("Simulation Logs")

    if not os.path.exists(LOG_FILE):
        st.info("No Logs Available")
        return

    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    st.download_button(
        "Download Logs (JSON)",
        data=json.dumps(logs, indent=2),
        file_name="simulation_logs.json",
        mime="application/json"
    )
    
    with st.expander("View Raw Logs (JSON)", expanded=False):
        st.json(logs)

    # Header
    cols = st.columns([2, 2, 2, 4])
    cols[0].markdown("**Timestamp**")
    cols[1].markdown("**Event Type**")
    cols[2].markdown("**Email**")
    cols[3].markdown("**Details**")

    # Rows
    for entry in logs:
        cols = st.columns([2, 2, 2, 4])
        cols[0].write(entry.get("timestamp"))
        cols[1].write(entry.get("event_type"))
        cols[2].write(entry.get("data", {}).get("email"))
        cols[3].write(str(entry.get("data", {})))

    
