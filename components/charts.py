import streamlit as st
import plotly.graph_objects as go
from services.simulation_service import get_report

def render_intent_pie():
    report = get_report()
    
    worried = report["intent_breakdown"]["worried_curious"]
    dismissive = report["intent_breakdown"]["unbothered_dismissive"]
    
    if worried + dismissive == 0:
        st.info("No responses yet to visualize intent")
        return

    labels = ["Worried / Curious", "Unbothered / Dismissive"]
    values = [worried, dismissive]
    
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                pull=[0.05, 0],
                textinfo="percent+label"
            )
        ]
    )
    
    fig.update_layout(
        title="User Intent Distribution",
        showlegend=True
    )
    
    st.plotly_chart(fig, width="stretch")
