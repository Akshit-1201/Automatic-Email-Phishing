import streamlit as st
from services.simulation_service import send_reminders

def render_reminders():
    st.subheader("Reminder Engine")
    
    if st.button("Send Reminders to Non-Responders"):
        send_reminders()
        st.success("Reminders sent successfully!")