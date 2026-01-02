import streamlit as st
import os
from services.simulation_service import get_report, get_state
from components.charts import render_intent_pie

def render_dashboard():
    st.subheader("Live Simulation Stats")

    report = get_report()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Targets", report["total_targets"])
    col2.metric("Responded", report["responded"])
    col3.metric("Pending", report["pending"])
    col4.metric("Max Retries", report["no_response_after_retries"])
    col5.metric("Response Rate", report["response_rate"])

    st.divider()
    render_intent_pie()

    # 🔐 Credential Capture Links Section
    st.divider()
    st.subheader("🔐 Credential Capture Links")

    google_form_url = os.getenv("GOOGLE_FORM_URL")

    if not google_form_url:
        st.warning("No credential capture link configured")
        return

    users = get_state()

    recipients = [
        email for email, data in users.items()
        if data.get("intent") == "worried_curious"
    ]

    st.markdown("**Active Credential Capture Link:**")
    st.code(google_form_url)

    st.markdown(f"**Sent to {len(recipients)} user(s)**")

    # ✅ SAFE TABLE (no st.table / no st.dataframe)
    if recipients:
        header = st.columns([4])
        header[0].markdown("**Recipient Email**")

        for email in recipients:
            row = st.columns([4])
            row[0].write(email)
