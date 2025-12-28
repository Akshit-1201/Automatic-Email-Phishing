import streamlit as st
from services.simulation_service import start_simulation, process_responses, send_reminders
# from services.simulation_service import send_reminders


def render_controls():
    st.subheader("Simulation controls")
    
    emails = st.text_area(
        "Target Emails (comma-separated)",
        placeholder="user1@email.com, user2@email.com"
    )
    
    col1, col2, col3  = st.columns(3)
    
    # Start Button
    if col1.button("Start Simulation"):
        email_list = [e.strip() for e in emails.split(",") if e.strip()]
        start_simulation(email_list)
        st.success("Inital Emails Sent")
    
    # Processing Button
    if col2.button("Process Responses"):
        process_responses()
        st.success("Responses Processes")
        
    # Reminders Button
    if st.button("Send Reminders to Non-Responders"):
        send_reminders()
        st.success("Reminders sent successfully!")