import streamlit as st

def render_health_score_gauge(score: int):
    """
    Render a health score as a gauge/progress bar with color and label.
    Args:
        score (int): Health score from 0 to 100.
    """
    # Determine color based on score
    if score >= 80:
        color = '#28a745'  # Green
        status = 'Excellent'
        emoji = '🟢'
    elif score >= 60:
        color = '#ffc107'  # Yellow
        status = 'Good'
        emoji = '🟡'
    elif score >= 40:
        color = '#fd7e14'  # Orange
        status = 'Fair'
        emoji = '🟠'
    else:
        color = '#dc3545'  # Red
        status = 'Poor'
        emoji = '🔴'

    st.markdown(f"""
    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #e9ecef; background: #f8f9fa;">
        <div style="font-size: 1.2em; font-weight: bold; color: {color};">
            {emoji} Health Score: {score}/100
        </div>
        <div style="height: 18px; background: #e9ecef; border-radius: 9px; margin: 0.5em 0;">
            <div style="width: {score}%; height: 100%; background: {color}; border-radius: 9px;"></div>
        </div>
        <div style="font-size: 0.95em; color: #666;">Status: <b>{status}</b></div>
    </div>
    """, unsafe_allow_html=True) 