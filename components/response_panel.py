import streamlit as st
from services.simulation_service import get_state
import pandas as pd

def render_responses():
    st.header("👥 User Responses")
    st.markdown("Track individual user interactions and status")
    
    try:
        users = get_state()
        
        if not users:
            st.info("📭 No users in simulation yet. Start a simulation to track responses.")
            return
        
        # Convert to DataFrame for better display
        user_data = []
        for email, data in users.items():
            user_data.append({
                "Email": email,
                "Status": data.get("status", "unknown"),
                "Intent": data.get("intent", "pending") or "pending",
                "Retries": data.get("retry_count", 0),
                "Template": data.get("template_name", "N/A"),
                "Created": data.get("created_at", "N/A")
            })
        
        df = pd.DataFrame(user_data)
        
        # Summary Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users))
        
        with col2:
            responded = len([u for u in users.values() if u.get("status") == "responded"])
            st.metric("Responded", responded)
        
        with col3:
            worried = len([u for u in users.values() if u.get("intent") == "worried_curious"])
            st.metric("Worried/Curious", worried)
        
        with col4:
            dismissive = len([u for u in users.values() if u.get("intent") == "unbothered_dismissive"])
            st.metric("Dismissive", dismissive)
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Filter Users")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=df["Status"].unique().tolist(),
                default=df["Status"].unique().tolist()
            )
        
        with col2:
            intent_filter = st.multiselect(
                "Filter by Intent",
                options=df["Intent"].unique().tolist(),
                default=df["Intent"].unique().tolist()
            )
        
        with col3:
            search_email = st.text_input("Search Email", placeholder="user@example.com")
        
        # Apply Filters
        filtered_df = df[df["Status"].isin(status_filter) & df["Intent"].isin(intent_filter)]
        
        if search_email:
            filtered_df = filtered_df[filtered_df["Email"].str.contains(search_email, case=False)]
        
        st.markdown("---")
        
        # Display Table
        st.subheader(f"📋 User Details ({len(filtered_df)} users)")
        
        # Style the dataframe
        def highlight_status(val):
            if val == "responded":
                return 'background-color: #90EE90'
            elif val == "max_retries_reached":
                return 'background-color: #FFB6C1'
            elif val == "initial_sent":
                return 'background-color: #ADD8E6'
            return ''
        
        def highlight_intent(val):
            if val == "worried_curious":
                return 'background-color: #FFFFE0'
            elif val == "unbothered_dismissive":
                return 'background-color: #E0E0E0'
            return ''
        
        styled_df = filtered_df.style.applymap(highlight_status, subset=['Status']) \
                                     .applymap(highlight_intent, subset=['Intent'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Legend
        with st.expander("📖 Status Legend"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Status Colors:**")
                st.markdown("🟢 `responded` - User replied")
                st.markdown("🔵 `initial_sent` - Initial email sent")
                st.markdown("🔴 `max_retries_reached` - No response after 3 reminders")
            
            with col2:
                st.markdown("**Intent Colors:**")
                st.markdown("🟡 `worried_curious` - Showing concern")
                st.markdown("⚪ `unbothered_dismissive` - Not concerned")
                st.markdown("⚫ `pending` - Not yet classified")
        
        # Detailed User History
        st.markdown("---")
        st.subheader("📜 User History")
        
        selected_email = st.selectbox(
            "Select user to view detailed history:",
            options=["Select a user..."] + list(users.keys())
        )
        
        if selected_email != "Select a user...":
            user = users[selected_email]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Email:** {selected_email}")
                st.markdown(f"**Status:** {user.get('status', 'unknown')}")
                st.markdown(f"**Intent:** {user.get('intent', 'pending') or 'pending'}")
            
            with col2:
                st.markdown(f"**Template:** {user.get('template_name', 'N/A')}")
                st.markdown(f"**Retry Count:** {user.get('retry_count', 0)}")
                st.markdown(f"**Created:** {user.get('created_at', 'N/A')}")
            
            # Event History
            history = user.get('history', [])
            if history:
                st.markdown("**Event Timeline:**")
                for event in history:
                    timestamp = event.get('timestamp', 'N/A')
                    event_type = event.get('event', 'unknown')
                    details = event.get('details', {})
                    
                    with st.expander(f"🕒 {timestamp} - {event_type}"):
                        st.json(details)
            else:
                st.info("No event history available")
        
        # Export Option
        st.markdown("---")
        if st.button("📥 Export User Data (CSV)"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="simulation_users.csv",
                mime="text/csv"
            )
        
        # Raw JSON View
        with st.expander("🔧 View Raw JSON Data"):
            st.json(users)
    
    except Exception as e:
        st.error(f"❌ Error loading user responses: {str(e)}")