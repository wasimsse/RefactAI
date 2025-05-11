import streamlit as st

def render_metrics_chart(metrics: dict):
    """Render a bar or radar chart for metrics visualization."""
    try:
        import plotly.graph_objects as go
        # Only use metrics that are in max_values
        max_values = {
            "lcom": 1.0,
            "cbo": 10.0,
            "dit": 5.0,
            "cc": 15.0,
            "rfc": 30.0
        }
        filtered_metrics = {k: v for k, v in metrics.items() if k in max_values}
        if not filtered_metrics:
            st.warning("No complexity metrics available for chart.")
            return None
        norm_metrics = {k: min(v["value"] / max_values[k], 1.0) for k, v in filtered_metrics.items()}
        categories = list(norm_metrics.keys())
        values = list(norm_metrics.values())
        thresholds = [filtered_metrics[k]["threshold"] / max_values[k] for k in categories]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Values'
        ))
        fig.add_trace(go.Scatterpolar(
            r=thresholds,
            theta=categories,
            fill='toself',
            name='Thresholds',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='red', dash='dot')
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="Complexity Metrics Overview (Normalized)",
            height=400
        )
        return fig
    except ImportError:
        import pandas as pd
        max_values = {
            "lcom": 1.0,
            "cbo": 10.0,
            "dit": 5.0,
            "cc": 15.0,
            "rfc": 30.0
        }
        filtered_metrics = {k: v for k, v in metrics.items() if k in max_values}
        if not filtered_metrics:
            st.warning("No complexity metrics available for chart.")
            return None
        chart_data = pd.DataFrame({
            'Metric': list(filtered_metrics.keys()),
            'Value': [m["value"] for m in filtered_metrics.values()],
            'Threshold': [m["threshold"] for m in filtered_metrics.values()]
        })
        return chart_data
    except Exception as e:
        st.error(f"Could not render metrics chart: {str(e)}")
        return None 