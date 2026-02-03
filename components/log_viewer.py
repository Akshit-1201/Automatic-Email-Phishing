import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

LOG_FILE = "simulation_log.json"

def render_logs():
    st.header("📜 Simulation Logs")
    st.markdown("View detailed system events and activities")
    
    if not os.path.exists(LOG_FILE):
        st.info("📭 No logs available yet. Logs will appear after simulation activities.")
        return
    
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
        
        if not logs:
            st.info("📭 Log file is empty")
            return
        
        # Summary Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", len(logs))
        
        with col2:
            initial_emails = len([l for l in logs if l.get("event_type") == "initial_email_sent"])
            st.metric("Initial Emails", initial_emails)
        
        with col3:
            responses = len([l for l in logs if l.get("event_type") == "response_processed"])
            st.metric("Responses", responses)
        
        with col4:
            reminders = len([l for l in logs if l.get("event_type") == "reminder_sent"])
            st.metric("Reminders", reminders)
        
        st.markdown("---")
        
        # Filter Options
        st.subheader("🔍 Filter Logs")
        
        col1, col2, col3 = st.columns(3)
        
        # Get unique event types
        event_types = list(set([log.get("event_type", "unknown") for log in logs]))
        
        with col1:
            selected_events = st.multiselect(
                "Event Type",
                options=event_types,
                default=event_types
            )
        
        with col2:
            # Get unique emails from logs
            emails_in_logs = set()
            for log in logs:
                email = log.get("data", {}).get("email")
                if email:
                    emails_in_logs.add(email)
            
            selected_emails = st.multiselect(
                "Filter by Email",
                options=list(emails_in_logs),
                default=[]
            )
        
        with col3:
            search_text = st.text_input("Search in logs", placeholder="Search keyword...")
        
        # Apply Filters
        filtered_logs = [
            log for log in logs
            if log.get("event_type") in selected_events
        ]
        
        if selected_emails:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("data", {}).get("email") in selected_emails
            ]
        
        if search_text:
            search_lower = search_text.lower()
            filtered_logs = [
                log for log in filtered_logs
                if search_lower in str(log).lower()
            ]
        
        st.markdown("---")
        
        # Download Buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download All Logs (JSON)",
                data=json.dumps(logs, indent=2),
                file_name="simulation_logs.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            if filtered_logs:
                st.download_button(
                    label="📥 Download Filtered Logs (JSON)",
                    data=json.dumps(filtered_logs, indent=2),
                    file_name="filtered_simulation_logs.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        st.markdown("---")
        
        # Display Logs
        st.subheader(f"📋 Event Log ({len(filtered_logs)} entries)")
        
        if not filtered_logs:
            st.warning("No logs match your filters")
            return
        
        # Reverse to show newest first
        filtered_logs_reversed = list(reversed(filtered_logs))
        
        # Event type colors
        event_colors = {
            "initial_email_sent": "🟢",
            "response_processed": "🔵",
            "reminder_sent": "🟡",
            "followup_sent": "🟣",
            "max_retries": "🔴",
            "error": "⛔"
        }
        
        # Display each log entry
        for idx, entry in enumerate(filtered_logs_reversed):
            timestamp = entry.get("timestamp", "N/A")
            event_type = entry.get("event_type", "unknown")
            data = entry.get("data", {})
            
            # Get color emoji
            color = event_colors.get(event_type, "⚪")
            
            # Create expander for each log entry
            with st.expander(f"{color} {timestamp} - {event_type}"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("**Event Type:**")
                    st.markdown("**Timestamp:**")
                    if data.get("email"):
                        st.markdown("**Email:**")
                
                with col2:
                    st.markdown(f"`{event_type}`")
                    st.markdown(f"`{timestamp}`")
                    if data.get("email"):
                        st.markdown(f"`{data.get('email')}`")
                
                st.markdown("**Event Data:**")
                st.json(data)
        
        # Raw JSON View
        st.markdown("---")
        with st.expander("🔧 View Raw JSON (All Logs)", expanded=False):
            st.json(logs)
        
        # Event Type Legend
        with st.expander("📖 Event Type Legend"):
            st.markdown("""
            - 🟢 **initial_email_sent**: Initial phishing email sent to target
            - 🔵 **response_processed**: User response received and classified
            - 🟡 **reminder_sent**: Reminder email sent to non-responder
            - 🟣 **followup_sent**: Follow-up email sent based on intent
            - 🔴 **max_retries**: User reached maximum retry limit
            - ⛔ **error**: System error occurred
            """)
    
    except json.JSONDecodeError:
        st.error("❌ Error: Log file is corrupted or contains invalid JSON")
    except Exception as e:
        st.error(f"❌ Error loading logs: {str(e)}")