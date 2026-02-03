import streamlit as st
from components.dashboard import render_dashboard
from components.controls import render_controls
from components.response_panel import render_responses
from components.log_viewer import render_logs

st.set_page_config(
    page_title="Phishing Simulation Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #145a8c;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🛡️ Phishing Simulation Control Panel</div>', unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.title("🎯 Navigation")
    st.markdown("---")
    
    page = st.radio(
        "Select View:",
        ["📊 Dashboard", "🎮 Controls", "👥 User Responses", "📜 Logs"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Use the refresh button below to update data manually")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.caption("⚠️ Educational Use Only")

# Render selected page
if page == "📊 Dashboard":
    render_dashboard()
    
elif page == "🎮 Controls":
    render_controls()
    
elif page == "👥 User Responses":
    render_responses()
    
elif page == "📜 Logs":
    render_logs()

# Footer
st.markdown("---")
st.caption("Built for cybersecurity education | Author: Akshit Negi")