import streamlit as st
import os
from services.simulation_service import get_report, get_state
from components.charts import render_intent_pie

def render_dashboard():
    st.header("📊 Live Simulation Statistics")
    
    try:
        report = get_report()
        
        # Main Metrics Row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="🎯 Total Targets",
                value=report["total_targets"],
                help="Total number of users in the simulation"
            )
        
        with col2:
            st.metric(
                label="✅ Responded",
                value=report["responded"],
                delta=f"{report['response_rate']}" if report['total_targets'] > 0 else "0%",
                help="Users who replied to the email"
            )
        
        with col3:
            st.metric(
                label="⏳ Pending",
                value=report["pending"],
                help="Users who haven't responded yet"
            )
        
        with col4:
            st.metric(
                label="🔄 Max Retries",
                value=report["no_response_after_retries"],
                help="Users who didn't respond after 3 reminders"
            )
        
        with col5:
            st.metric(
                label="📈 Response Rate",
                value=report["response_rate"],
                help="Percentage of users who responded"
            )
        
        st.markdown("---")
        
        # Intent Distribution Chart
        st.subheader("🧠 User Intent Distribution")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            render_intent_pie()
        
        with col2:
            st.markdown("### Intent Categories")
            
            worried = report["intent_breakdown"]["worried_curious"]
            dismissive = report["intent_breakdown"]["unbothered_dismissive"]
            
            st.metric("😰 Worried / Curious", worried)
            st.caption("Users showing concern or asking questions")
            
            st.metric("😐 Unbothered / Dismissive", dismissive)
            st.caption("Users showing no concern")
        
        st.markdown("---")
        
        # Credential Capture Section
        st.subheader("🔐 Credential Capture Links")
        
        google_form_url = os.getenv("GOOGLE_FORM_URL")
        
        if google_form_url:
            users = get_state()
            
            recipients = [
                email for email, data in users.items()
                if data.get("intent") == "worried_curious"
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Active Link:** {google_form_url}")
                st.caption(f"📤 Sent to **{len(recipients)}** worried/curious user(s)")
            
            with col2:
                if recipients:
                    with st.expander(f"👥 View Recipients ({len(recipients)})"):
                        for email in recipients:
                            st.write(f"• {email}")
                else:
                    st.warning("No worried/curious users yet")
        else:
            st.warning("⚠️ No credential capture link configured in .env file")
            st.caption("Set GOOGLE_FORM_URL in your .env file to enable this feature")
        
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")
        st.info("Start a simulation to see statistics here")