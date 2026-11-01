"""
FactoryPulse AI - Industrial Plotly Visualizations & Charts
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

CHART_THEME = {
    "plot_bgcolor": "rgba(20, 27, 36, 0.9)",
    "paper_bgcolor": "rgba(15, 20, 28, 0.0)",
    "font": {"color": "#cbd5e1", "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": "#222f3e", "zerolinecolor": "#222f3e"},
    "yaxis": {"gridcolor": "#222f3e", "zerolinecolor": "#222f3e"},
    "margin": {"l": 40, "r": 20, "t": 35, "b": 35},
}


def create_rpm_chart(readings: List[Dict[str, Any]]) -> go.Figure:
    """Create multi-station rotational speed (RPM) time-series plot."""
    fig = go.Figure()

    if not readings:
        fig.add_annotation(text="No RPM telemetry recorded yet", showarrow=False, font={"size": 14, "color": "#64748b"})
        fig.update_layout(**CHART_THEME, height=280)
        return fig

    df = pd.DataFrame(readings)
    colors = {
        "station01": "#38bdf8",  # Light blue
        "station02": "#f59e0b",  # Amber/Orange (Drilling focal)
        "station03": "#10b981",  # Emerald green
    }
    names = {
        "station01": "Station 1 (Cutting)",
        "station02": "Station 2 (Drilling / ESP32)",
        "station03": "Station 3 (Packaging)",
    }

    for st_id, group in df.groupby("station_id"):
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(group["timestamp"]),
            y=group["rpm"],
            mode="lines+markers",
            name=names.get(st_id, st_id),
            line={"color": colors.get(st_id, "#94a3b8"), "width": 2.5},
            marker={"size": 4},
        ))

    # Add nominal threshold lines
    fig.add_hline(y=1500, line_dash="dot", line_color="#475569", annotation_text="St2 Nominal (1500 RPM)")
    fig.add_hline(y=600, line_dash="dash", line_color="#ef4444", annotation_text="Critical Limit (600 RPM)")

    fig.update_layout(
        **CHART_THEME,
        title="<b>Machine Rotational Speed (RPM) vs Time</b>",
        height=300,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    return fig


def create_queue_chart(readings: List[Dict[str, Any]]) -> go.Figure:
    """Create buffer queue accumulation timeline chart."""
    fig = go.Figure()

    if not readings:
        fig.add_annotation(text="No buffer queue data available", showarrow=False, font={"size": 14, "color": "#64748b"})
        fig.update_layout(**CHART_THEME, height=260)
        return fig

    df = pd.DataFrame(readings)
    colors = {"station01": "#38bdf8", "station02": "#f59e0b", "station03": "#10b981"}

    for st_id, group in df.groupby("station_id"):
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(group["timestamp"]),
            y=group["queue_length"],
            mode="lines",
            fill="tozeroy",
            name=f"{st_id} Queue",
            line={"color": colors.get(st_id, "#94a3b8"), "width": 2},
        ))

    fig.add_hline(y=15, line_dash="dash", line_color="#f59e0b", annotation_text="Warning (15 units)")
    fig.add_hline(y=30, line_dash="dash", line_color="#ef4444", annotation_text="Critical (30 units)")

    fig.update_layout(
        **CHART_THEME,
        title="<b>Buffer Queue Accumulation (WIP) by Workstation</b>",
        height=280,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    return fig


def create_throughput_chart(line_metrics: List[Dict[str, Any]]) -> go.Figure:
    """Create Throughput vs Demand production line chart."""
    fig = go.Figure()

    if not line_metrics:
        fig.add_annotation(text="No production metrics recorded yet", showarrow=False, font={"size": 14, "color": "#64748b"})
        fig.update_layout(**CHART_THEME, height=260)
        return fig

    df = pd.DataFrame(line_metrics)
    ts = pd.to_datetime(df["timestamp"])

    fig.add_trace(go.Scatter(
        x=ts, y=df["demand_rate"],
        mode="lines", name="Target Demand Rate",
        line={"color": "#38bdf8", "dash": "dot", "width": 2},
    ))
    fig.add_trace(go.Scatter(
        x=ts, y=df["line_throughput"],
        mode="lines+markers", name="Actual Line Throughput",
        line={"color": "#10b981", "width": 3},
        marker={"size": 4},
    ))

    fig.update_layout(
        **CHART_THEME,
        title="<b>Factory Throughput vs Target Demand (Parts/min)</b>",
        height=280,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    return fig


def create_risk_gauge(probability: float) -> go.Figure:
    """Create AI Bottleneck Risk Gauge."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(probability * 100, 1),
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "<b>AI Bottleneck Risk (Next 60s)</b>", "font": {"size": 16, "color": "#f8fafc"}},
        number={"suffix": "%", "font": {"size": 32, "color": "#ffffff"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
            "bar": {"color": "#ef4444" if probability >= 0.7 else ("#f59e0b" if probability >= 0.4 else "#10b981")},
            "bgcolor": "#1e293b",
            "borderwidth": 1,
            "bordercolor": "#334155",
            "steps": [
                {"range": [0, 40], "color": "rgba(16, 185, 129, 0.2)"},
                {"range": [40, 70], "color": "rgba(245, 158, 11, 0.2)"},
                {"range": [70, 100], "color": "rgba(239, 68, 68, 0.2)"},
            ],
            "threshold": {
                "line": {"color": "#ff3838", "width": 3},
                "thickness": 0.8,
                "value": 70,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
        height=240,
        margin={"l": 25, "r": 25, "t": 35, "b": 10},
    )
    return fig


def create_confusion_matrix_chart(cm: List[List[int]]) -> go.Figure:
    """Create formatted heatmap for model confusion matrix."""
    z = cm
    x = ["Predicted Normal (0)", "Predicted Bottleneck (1)"]
    y = ["Actual Normal (0)", "Actual Bottleneck (1)"]

    fig = px.imshow(
        z, x=x, y=y,
        color_continuous_scale="Blues",
        text_auto=True,
    )
    fig.update_layout(
        **CHART_THEME,
        title="<b>Random Forest Evaluation Confusion Matrix</b>",
        height=320,
    )
    return fig

