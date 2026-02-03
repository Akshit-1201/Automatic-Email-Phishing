import streamlit as st
from services.simulation_service import start_simulation, process_responses, send_reminders, get_templates

def render_controls():
    st.header("🎮 Simulation Controls")
    st.markdown("Configure and control your phishing simulation campaign")
    
    # Template Selection Section
    st.subheader("1️⃣ Select Email Template")
    
    try:
        templates = get_templates()
        
        if not templates:
            st.error("❌ No templates found. Please check your templates configuration.")
            return
        
        # Create template options
        template_options = {
            f"{t['name']} ({t['category']})": t['id'] 
            for t in templates
        }
        
        selected_template_name = st.selectbox(
            "Choose a phishing template:",
            options=list(template_options.keys()),
            help="Select which type of phishing email to send"
        )
        
        selected_template_id = template_options[selected_template_name]
        
        # Show template preview
        with st.expander("👁️ Preview Template"):
            selected_template = next(t for t in templates if t['id'] == selected_template_id)
            st.markdown(f"**Name:** {selected_template['name']}")
            st.markdown(f"**Category:** {selected_template['category']}")
            
        st.markdown("---")
        
        # Target Emails Section
        st.subheader("2️⃣ Enter Target Emails")
        
        emails = st.text_area(
            "Target Emails (one per line or comma-separated)",
            placeholder="user1@example.com\nuser2@example.com\nuser3@example.com",
            height=120,
            help="Enter email addresses of simulation targets"
        )
        
        st.markdown("---")
        
        # Control Buttons
        st.subheader("3️⃣ Execute Actions")
        
        col1, col2, col3 = st.columns(3)
        
        # Start Simulation Button
        with col1:
            if st.button("🚀 Start Simulation", use_container_width=True, type="primary"):
                if not emails.strip():
                    st.error("❌ Please enter at least one email address")
                else:
                    # Parse emails (handle both comma and newline separation)
                    email_list = []
                    for line in emails.split('\n'):
                        for email in line.split(','):
                            email = email.strip()
                            if email and '@' in email:
                                email_list.append(email)
                    
                    if not email_list:
                        st.error("❌ No valid email addresses found")
                    else:
                        with st.spinner(f"Sending initial emails to {len(email_list)} target(s)..."):
                            try:
                                start_simulation(email_list, selected_template_id)
                                st.success(f"✅ Initial emails sent to {len(email_list)} target(s)!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
        
        # Process Responses Button
        with col2:
            if st.button("📧 Process Responses", use_container_width=True):
                with st.spinner("Processing incoming responses..."):
                    try:
                        process_responses()
                        st.success("✅ Responses processed successfully!")
                    except Exception as e:
                        st.error(f"❌ Error processing responses: {str(e)}")
        
        # Send Reminders Button
        with col3:
            if st.button("🔔 Send Reminders", use_container_width=True):
                with st.spinner("Sending reminders to non-responders..."):
                    try:
                        send_reminders()
                        st.success("✅ Reminders sent successfully!")
                    except Exception as e:
                        st.error(f"❌ Error sending reminders: {str(e)}")
        
        # Help Section
        st.markdown("---")
        st.info("""
        **📖 How to use:**
        1. **Select Template**: Choose the type of phishing email
        2. **Enter Emails**: Add target email addresses
        3. **Start Simulation**: Send initial emails
        4. **Process Responses**: Analyze incoming replies and send follow-ups
        5. **Send Reminders**: Remind non-responders (up to 3 times)
        """)
        
    except Exception as e:
        st.error(f"❌ Error loading templates: {str(e)}")
        st.info("Please ensure your templates are configured correctly in templates/email_templates.json")