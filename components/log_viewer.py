import streamlit as st
import json
import os

LOG_FILE = "simulation_log.json"

def render_logs():
    st.subheader("Simulation Logs")
    
    if not os.path.exists(LOG_FILE):
        st.info("No Logs Available")
        return
    
    with open(LOG_FILE) as f:
        logs = json.load(f)
        
    st.json(logs)
    
    st.download_button(
        "Download Logs",
        data=json.dumps(logs, indent=2),
        file_name="simulation_logs.json",
        mime="application/json"
    )
    
    with st.expander("View Logs", expanded=False):
        st.json(logs)