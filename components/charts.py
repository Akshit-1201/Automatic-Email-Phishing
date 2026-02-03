import streamlit as st
import plotly.graph_objects as go
from services.simulation_service import get_report

def render_intent_pie():
    """Render intent distribution pie chart"""
    try:
        report = get_report()
        
        worried = report["intent_breakdown"]["worried_curious"]
        dismissive = report["intent_breakdown"]["unbothered_dismissive"]
        
        total_classified = worried + dismissive
        
        if total_classified == 0:
            st.info("📊 No classified responses yet. Chart will appear after processing user responses.")
            return
        
        labels = ["😰 Worried / Curious", "😐 Unbothered / Dismissive"]
        values = [worried, dismissive]
        colors = ['#FFD700', '#C0C0C0']  # Gold and Silver
        
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    pull=[0.05, 0],
                    textinfo="percent+label+value",
                    textfont=dict(size=14),
                    marker=dict(
                        colors=colors,
                        line=dict(color='white', width=2)
                    ),
                    hovertemplate="<b>%{label}</b><br>" +
                                  "Count: %{value}<br>" +
                                  "Percentage: %{percent}<br>" +
                                  "<extra></extra>"
                )
            ]
        )
        
        fig.update_layout(
            title={
                'text': "User Intent Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#1f77b4'}
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            height=400,
            annotations=[
                dict(
                    text=f'Total<br>{total_classified}',
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False
                )
            ]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error rendering chart: {str(e)}")

def render_status_bar():
    """Render status distribution bar chart"""
    try:
        report = get_report()
        
        categories = ['Responded', 'Pending', 'Max Retries']
        values = [
            report['responded'],
            report['pending'],
            report['no_response_after_retries']
        ]
        colors = ['#90EE90', '#ADD8E6', '#FFB6C1']
        
        fig = go.Figure(
            data=[
                go.Bar(
                    x=categories,
                    y=values,
                    marker_color=colors,
                    text=values,
                    textposition='auto',
                    hovertemplate="<b>%{x}</b><br>" +
                                  "Count: %{y}<br>" +
                                  "<extra></extra>"
                )
            ]
        )
        
        fig.update_layout(
            title={
                'text': "Response Status Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#1f77b4'}
            },
            xaxis_title="Status",
            yaxis_title="Number of Users",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error rendering status chart: {str(e)}")