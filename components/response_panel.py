import streamlit as st
from services.simulation_service import get_state

def render_responses():
    st.subheader("User Responses")

    users = get_state()

    if not users:
        st.info("No users in simulation yet")
        return

    # Table header
    cols = st.columns([3, 2, 2, 1, 3])
    cols[0].markdown("**Email**")
    cols[1].markdown("**Status**")
    cols[2].markdown("**Intent**")
    cols[3].markdown("**Retries**")
    cols[4].markdown("**Created At**")

    # Table rows
    for email, data in users.items():
        cols = st.columns([3, 2, 2, 1, 3])
        cols[0].write(email)
        cols[1].write(data.get("status"))
        cols[2].write(data.get("intent"))
        cols[3].write(data.get("retry_count"))
        cols[4].write(data.get("created_at"))

    # Optional raw JSON
    with st.expander("View Raw User State (JSON)", expanded=False):
        st.json(users)
