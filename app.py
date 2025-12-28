import streamlit as st
import time
from components.dashboard import render_dashboard
from components.controls import render_controls
from components.response_panel import render_responses
# from components.reminder_panel import render_reminders
from components.log_viewer import render_logs
# from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Phishing Simulation Dashboard",
    layout="wide"
)

st.title("Phishing Simulation Control Panel")

render_dashboard()
render_controls()
render_responses()
# render_reminders()
render_logs()

# st_autorefresh(interval=5_000, key="phishing_refresh")
time.sleep(5)
st.rerun()
