import streamlit as st
import plotly.graph_objects as go
import time

def render_metric_category_chart(metrics: dict, category: str, keys: list):
    """
    Render a chart for a specific metric category, using the best chart type for that category.
    Args:
        metrics (dict): All metrics.
        category (str): Category name for the chart title.
        keys (list): List of metric keys to include in the chart.
    """
    category = category.lower()
    if category == "complexity":
        return render_complexity_radar_chart(metrics, keys)
    elif category == "size":
        return render_size_bar_chart(metrics, keys)
    elif category == "structure":
        return render_structure_bar_chart(metrics, keys)
    elif category == "documentation":
        return render_documentation_gauge(metrics, keys)
    else:
        st.warning(f"No chart type defined for {category} metrics.")
        return None

def render_complexity_radar_chart(metrics: dict, keys: list):
    try:
        filtered_metrics = {k: v for k, v in metrics.items() if k in keys}
        if not filtered_metrics:
            st.warning("No complexity metrics available for chart.")
            return None
        max_values = {"lcom": 1.0, "cbo": 10.0, "dit": 5.0, "cc": 15.0, "rfc": 30.0}
        norm_metrics = {k: min(v["value"] / max_values.get(k, 1.0), 1.0) for k, v in filtered_metrics.items()}
        categories = list(norm_metrics.keys())
        values = list(norm_metrics.values())
        thresholds = [filtered_metrics[k].get("threshold", max_values.get(k, 1.0)) / max_values.get(k, 1.0) for k in categories]
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
        st.plotly_chart(fig, use_container_width=True, key="complexity_metrics_chart")
        return fig
    except Exception as e:
        st.error(f"Could not render complexity metrics chart: {str(e)}")
        return None

def render_size_bar_chart(metrics: dict, keys: list):
    import pandas as pd
    filtered_metrics = {k: v for k, v in metrics.items() if k in keys}
    if not filtered_metrics:
        st.warning("No size metrics available for chart.")
        return None
    chart_data = pd.DataFrame({
        'Metric': list(filtered_metrics.keys()),
        'Value': [m["value"] for m in filtered_metrics.values()]
    })
    st.bar_chart(chart_data.set_index('Metric')[['Value']])
    return chart_data

def render_structure_bar_chart(metrics: dict, keys: list):
    import pandas as pd
    filtered_metrics = {k: v for k, v in metrics.items() if k in keys}
    if not filtered_metrics:
        st.warning("No structure metrics available for chart.")
        return None
    chart_data = pd.DataFrame({
        'Metric': list(filtered_metrics.keys()),
        'Value': [m["value"] for m in filtered_metrics.values()]
    })
    st.bar_chart(chart_data.set_index('Metric')[['Value']])
    return chart_data

def render_documentation_gauge(metrics: dict, keys: list):
    # Only one metric: comment_density
    metric = keys[0] if keys else None
    if not metric or metric not in metrics:
        st.warning("No documentation metrics available for chart.")
        return None
    value = metrics[metric]["value"]
    color = '#28a745' if value >= 60 else '#ffc107' if value >= 30 else '#dc3545'
    st.markdown(f"""
    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #e9ecef; background: #f8f9fa; width: 90%;">
        <div style="font-size: 1.1em; font-weight: bold; color: {color};">
            📝 Comment Density: {value}%
        </div>
        <div style="height: 18px; background: #e9ecef; border-radius: 9px; margin: 0.5em 0;">
            <div style="width: {value}%; height: 100%; background: {color}; border-radius: 9px;"></div>
        </div>
        <div style="font-size: 0.95em; color: #666;">Status: <b>{'Good' if value >= 60 else 'Fair' if value >= 30 else 'Poor'}</b></div>
    </div>
    """, unsafe_allow_html=True)
    return value

def render_metrics_chart(metrics: dict):
    # For backward compatibility: only renders complexity metrics
    return render_metric_category_chart(
        metrics,
        category="Complexity",
        keys=["lcom", "cbo", "dit", "cc", "rfc"]
    )

def animated_bar_chart(metrics, category, keys):
    values = [metrics[k]["value"] for k in keys]
    fig = go.Figure(
        data=[go.Bar(x=keys, y=[0]*len(keys), marker_color='indianred')],
        layout=go.Layout(
            title=f"{category} Metrics (Animated)",
            yaxis=dict(range=[0, max(values)*1.2])
        )
    )
    chart = st.plotly_chart(fig, use_container_width=True)
    for i in range(1, 11):
        y = [v * i / 10 for v in values]
        fig.data[0].y = y
        chart.plotly_chart(fig, use_container_width=True)
        time.sleep(0.05)

def animated_radar_chart(metrics, keys, title="Radar Chart"):
    values = [metrics[k]["value"] for k in keys]
    categories = keys + [keys[0]]
    values = values + [values[0]]
    fig = go.Figure()
    radar = go.Scatterpolar(r=[0]*len(categories), theta=categories, fill='toself', name='Metrics')
    fig.add_trace(radar)
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values)*1.2])),
        showlegend=False,
        title=title
    )
    chart = st.plotly_chart(fig, use_container_width=True)
    for i in range(1, 11):
        r = [v * i / 10 for v in values]
        fig.data[0].r = r
        chart.plotly_chart(fig, use_container_width=True)
        time.sleep(0.05) 