import streamlit as st
from services.simulation_service import get_state

def render_responses():
    st.subheader("User Responses")
    
    users = get_state()
    
    for email, data in users.items():
        with st.expander(email):
            st.write("Status:", data["status"])
            st.write("Intent:", data.get("intent"))
            st.write("Retries:", data["retry_count"])
            st.json(data["history"])