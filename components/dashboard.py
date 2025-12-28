import streamlit as st
from services.simulation_service import get_report
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