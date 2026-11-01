"""
FactoryPulse AI — Smart Factory Bottleneck Prediction Dashboard
A multi-page industrial operations and machine learning control system.
"""

import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# Setup page layout
st.set_page_config(
    page_title="FactoryPulse AI — Bottleneck Prediction",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Core imports
from src.common.config import config
from src.common.auth import authenticate_user, seed_default_users
from src.database.db import db
from src.simulator.factory_simulator import FactorySimulator
from src.alerts.engine import alert_engine
from src.prediction.predictor import RealTimePredictor
from src.mqtt.client import MQTTClientWrapper
from dashboard.components.styles import INDUSTRIAL_THEME_CSS
from dashboard.components.charts import (
    create_rpm_chart,
    create_queue_chart,
    create_throughput_chart,
    create_risk_gauge,
    create_confusion_matrix_chart,
)

# Inject Dark Theme CSS
st.markdown(INDUSTRIAL_THEME_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"

if "simulator" not in st.session_state:
    st.session_state.simulator = FactorySimulator()
    st.session_state.sim_running = True
    st.session_state.predictor = RealTimePredictor()
    st.session_state.mqtt_client = MQTTClientWrapper(client_id_suffix="dashboard")
    st.session_state.mqtt_client.connect(timeout=2.0)
    seed_default_users()


def step_simulation():
    """Advance simulation one step, persist to SQLite, check alerts, and run AI inference."""
    if st.session_state.sim_running:
        step = st.session_state.simulator.step()
        # 1. Persist readings
        for st_id in ["station01", "station02", "station03"]:
            reading = step[st_id].model_dump()
            db.insert_sensor_reading(reading)
            # Check alerts
            alert_engine.evaluate_station_reading(reading)
            # Publish to MQTT
            st.session_state.mqtt_client.publish(f"factory/{st_id}/telemetry", reading)

        # 2. Persist line telemetry
        line_metric = step["processed"].model_dump()
        db.insert_production_metric(line_metric)
        st.session_state.mqtt_client.publish(config.TOPIC_PROCESSED, line_metric)

        # 3. Real-time AI prediction on focal Station 2
        st.session_state.predictor.process_reading(step["station02"].model_dump())


# Execute a step on dashboard refresh
step_simulation()

# ------------------------------------------------------------------------------
# Sidebar Navigation & Industrial Control Bar
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏭 FactoryPulse AI")
    st.caption("Smart Factory Bottleneck Prediction")
    st.markdown("---")

    # Authentication Status
    if st.session_state.authenticated:
        user = st.session_state.user
        role_color = "#38bdf8" if user.get("role") == "admin" else "#10b981"
        st.markdown(
            f"👤 **{user.get('full_name', user['username'])}**  \n"
            f"<span style='color:{role_color}; font-weight:600; text-transform:uppercase;'>[{user.get('role', 'operator')}]</span>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    else:
        st.info("🔐 Please log in to access all pages.")

    st.markdown("---")

    # Navigation Menu
    pages = [
        "Login",
        "Overview",
        "Live Monitoring",
        "Production Line",
        "AI Predictions",
        "Alerts",
        "Historical Analytics",
        "Model Performance",
        "Device Management",
        "Settings",
    ]

    selected_page = st.radio("Navigation", pages, index=pages.index(st.session_state.current_page))
    st.session_state.current_page = selected_page

    st.markdown("---")

    # Simulation Quick Controls
    st.markdown("##### ⚙️ Simulation Controls")
    sim = st.session_state.simulator

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.session_state.sim_running:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.sim_running = False
                st.rerun()
        else:
            if st.button("▶️ Resume", use_container_width=True):
                st.session_state.sim_running = True
                st.rerun()

    with col_btn2:
        if st.button("🔄 Reset", use_container_width=True):
            sim.reset()
            st.success("Line reset!")
            st.rerun()

    scenario_options = list(FactorySimulator.SCENARIOS.keys())
    current_idx = scenario_options.index(sim.active_scenario) if sim.active_scenario in scenario_options else 0
    selected_scenario = st.selectbox(
        "Operating Scenario",
        scenario_options,
        index=current_idx,
        format_func=lambda k: FactorySimulator.SCENARIOS[k],
    )
    if selected_scenario != sim.active_scenario:
        sim.set_scenario(selected_scenario)
        st.rerun()

    # Time acceleration
    time_scale = st.slider("Time Scale", 1.0, 5.0, float(sim.time_scale), 0.5)
    sim.time_scale = time_scale

    st.markdown("---")
    # MQTT Broker Health Pill
    info = st.session_state.mqtt_client.connection_info
    mode_label = "HiveMQ Cloud" if info.get("mode") == "hivemq_cloud" else ("Mosquitto (1883)" if not info.get("in_process_fallback") else "In-Process Bus")
    st.caption(f"Broker: **{mode_label}**")
    st.caption(f"Status: 🟢 **Connected**")


# ------------------------------------------------------------------------------
# PAGE ROUTING
# ------------------------------------------------------------------------------

# 1. LOGIN PAGE
if st.session_state.current_page == "Login":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🔐 FactoryPulse AI — Authentication</div>
            <div class="factory-subtitle">Role-Based Access Control for Industrial Operators and Administrators</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        st.success(f"Already authenticated as **{st.session_state.user['username']}** ({st.session_state.user['role']}).")
        col_out1, col_out2 = st.columns([1, 4])
        with col_out1:
            if st.button("Log Out Now", type="primary"):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
    else:
        col_login, col_info = st.columns([1.2, 1])
        with col_login:
            st.markdown("#### Sign In to Workstation")
            with st.form("login_form"):
                username_input = st.text_input("Username", value="admin")
                password_input = st.text_input("Password", type="password", value="FactoryAdmin2026!")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    user = authenticate_user(username_input, password_input)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(f"Welcome back, {user.get('full_name')}!")
                        st.session_state.current_page = "Overview"
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please verify your username and password.")

        with col_info:
            st.markdown("""
            #### ℹ️ Pre-Configured Accounts
            For academic examination and demonstration:
            - **Administrator Account:**  
              Username: `admin`  
              Password: `FactoryAdmin2026!`  
              *Permissions: Full system control, model retraining, settings, alerts acknowledgment.*
            - **Plant Floor Operator Account:**  
              Username: `operator`  
              Password: `FactoryOp2026!`  
              *Permissions: Telemetry monitoring, alerts view, and basic controls.*
            """)


# 2. OVERVIEW PAGE
elif st.session_state.current_page == "Overview":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🏭 Factory Executive Overview</div>
            <div class="factory-subtitle">Production Health, Real-Time KPIs, and AI Bottleneck Risk</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    recent_metrics = db.get_recent_line_metrics(limit=1)
    metric = recent_metrics[-1] if recent_metrics else {
        "demand_rate": 15.0, "line_throughput": 15.0, "total_wip": 15, "bottleneck_station": None, "line_efficiency": 1.0
    }

    recent_preds = db.get_recent_predictions(limit=1)
    pred = recent_preds[0] if recent_preds else {"risk_probability": 0.05, "bottleneck_predicted": 0}

    # Top KPI Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Line Throughput</div>
            <div class="kpi-value">{metric.get('line_throughput', 0.0):.1f} <span style="font-size:14px; color:#94a3b8;">units/min</span></div>
            <div class="kpi-subtext" style="color:#00e676;">Target Demand: {metric.get('demand_rate', 0.0):.1f} PPM</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        eff_pct = metric.get('line_efficiency', 0.0) * 100
        eff_color = "#00e676" if eff_pct >= 85 else ("#ffb300" if eff_pct >= 60 else "#ff3d00")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Line Efficiency</div>
            <div class="kpi-value" style="color:{eff_color};">{eff_pct:.1f}%</div>
            <div class="kpi-subtext" style="color:#94a3b8;">Line Balance Ratio</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        wip = metric.get('total_wip', 0)
        wip_color = "#00e676" if wip < 20 else ("#ffb300" if wip < 35 else "#ff3d00")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Factory WIP</div>
            <div class="kpi-value" style="color:{wip_color};">{wip} <span style="font-size:14px; color:#94a3b8;">units</span></div>
            <div class="kpi-subtext" style="color:#94a3b8;">Across all 3 buffers</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        bn = metric.get('bottleneck_station')
        bn_text = bn if bn else "None (Balanced)"
        bn_badge = f"<span class='badge-critical'>{bn_text}</span>" if bn else "<span class='badge-normal'>Balanced</span>"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Active Constraint</div>
            <div class="kpi-value" style="font-size:20px; margin-top:4px;">{bn_badge}</div>
            <div class="kpi-subtext" style="color:#94a3b8;">Identified Bottleneck</div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary Visuals Row
    col_graph, col_gauge = st.columns([2, 1])
    with col_graph:
        readings = db.get_recent_readings(limit=90)
        st.plotly_chart(create_rpm_chart(readings), use_container_width=True)

    with col_gauge:
        risk = pred.get("risk_probability", 0.0)
        st.plotly_chart(create_risk_gauge(risk), use_container_width=True)
        if pred.get("bottleneck_predicted"):
            st.error(f"⚠️ **AI ALERT:** High bottleneck probability predicted within next 60s at **{pred.get('predicted_station', 'station02')}**!")
        else:
            st.success("✅ **AI Model:** Production line stable; low bottleneck risk for next 60s.")


# 3. LIVE MONITORING PAGE
elif st.session_state.current_page == "Live Monitoring":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">📊 Live Workstation Telemetry</div>
            <div class="factory-subtitle">Rotational Speeds, Processing Rates, and Sensor Readings</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    readings = db.get_recent_readings(limit=120)
    st.plotly_chart(create_rpm_chart(readings), use_container_width=True)

    # Live Station Metrics Grid
    st.markdown("#### Latest Station Snapshots")
    cols = st.columns(3)
    for i, st_id in enumerate(["station01", "station02", "station03"]):
        st_readings = [r for r in readings if r["station_id"] == st_id]
        latest = st_readings[-1] if st_readings else None

        with cols[i]:
            if latest:
                status = latest.get("status", "NORMAL")
                badge = f"<span class='badge-{status.lower()}'>{status}</span>"
                st.markdown(f"""
                <div class="station-card">
                    <div class="station-title">
                        <span>{latest.get('station_name', st_id)}</span>
                        {badge}
                    </div>
                    <div style="font-size:13px; color:#94a3b8; margin-bottom:8px;">
                        Source: <b>{latest.get('source', 'simulated').upper()}</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>Rotational Speed:</span>
                        <b>{latest.get('rpm', 0):.1f} RPM</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>Throughput:</span>
                        <b>{latest.get('throughput', 0):.1f} PPM</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>Cycle Time:</span>
                        <b>{latest.get('cycle_time', 0):.2f} sec</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>Upstream Queue:</span>
                        <b>{latest.get('queue_length', 0)} units</b>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span>Vibration / Temp:</span>
                        <span>{latest.get('vibration', 0):.1f} mm/s | {latest.get('temperature', 0):.0f}°C</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("#### Timestamped Telemetry Log")
    if readings:
        table_df = pd.DataFrame(readings)[["timestamp", "station_id", "source", "rpm", "throughput", "queue_length", "status"]]
        st.dataframe(table_df.tail(15), use_container_width=True)


# 4. PRODUCTION LINE PAGE
elif st.session_state.current_page == "Production Line":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🔄 Factory Production Line & Material Flow</div>
            <div class="factory-subtitle">Three-Stage Production Line Simulation & Buffer Queue Accumulation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sim = st.session_state.simulator
    c1, arrow1, c2, arrow2, c3 = st.columns([1.2, 0.2, 1.2, 0.2, 1.2])

    with c1:
        st1 = sim.station1
        fill_pct = min(100, int((st1.queue_length / 50.0) * 100))
        bar_color = "#00e676" if fill_pct < 35 else ("#ffb300" if fill_pct < 60 else "#ff3d00")
        st.markdown(f"""
        <div class="station-card">
            <div class="station-title">
                <span>1. Cutting Station</span>
                <span class="badge-{st1.status.lower()}">{st1.status}</span>
            </div>
            <p style="font-size:12px; color:#94a3b8;">Input Raw Material → Shear</p>
            <div>RPM: <b>{st1.current_rpm:.1f}</b></div>
            <div>Throughput: <b>{st1.current_throughput:.1f} PPM</b></div>
            <div style="margin-top:10px;">Queue: <b>{st1.queue_length}</b> / 50 units</div>
            <div class="queue-container">
                <div class="queue-fill" style="width:{fill_pct}%; background-color:{bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with arrow1:
        st.markdown("<div style='text-align:center; font-size:28px; padding-top:60px;'>➔</div>", unsafe_allow_html=True)

    with c2:
        st2 = sim.station2
        fill_pct2 = min(100, int((st2.queue_length / 50.0) * 100))
        bar_color2 = "#00e676" if fill_pct2 < 35 else ("#ffb300" if fill_pct2 < 60 else "#ff3d00")
        src_tag = "ESP32 HARDWARE" if st2.hardware_active else "SIMULATED"
        st.markdown(f"""
        <div class="station-card" style="border: 2px solid #f59e0b;">
            <div class="station-title">
                <span>2. Drilling / Machining</span>
                <span class="badge-{st2.status.lower()}">{st2.status}</span>
            </div>
            <p style="font-size:12px; color:#f59e0b; font-weight:600;">[{src_tag}]</p>
            <div>RPM: <b>{st2.current_rpm:.1f}</b></div>
            <div>Throughput: <b>{st2.current_throughput:.1f} PPM</b></div>
            <div style="margin-top:10px;">Queue: <b>{st2.queue_length}</b> / 50 units</div>
            <div class="queue-container">
                <div class="queue-fill" style="width:{fill_pct2}%; background-color:{bar_color2};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with arrow2:
        st.markdown("<div style='text-align:center; font-size:28px; padding-top:60px;'>➔</div>", unsafe_allow_html=True)

    with c3:
        st3 = sim.station3
        fill_pct3 = min(100, int((st3.queue_length / 50.0) * 100))
        bar_color3 = "#00e676" if fill_pct3 < 35 else ("#ffb300" if fill_pct3 < 60 else "#ff3d00")
        st.markdown(f"""
        <div class="station-card">
            <div class="station-title">
                <span>3. Packaging Station</span>
                <span class="badge-{st3.status.lower()}">{st3.status}</span>
            </div>
            <p style="font-size:12px; color:#94a3b8;">Output Finished Goods</p>
            <div>RPM: <b>{st3.current_rpm:.1f}</b></div>
            <div>Throughput: <b>{st3.current_throughput:.1f} PPM</b></div>
            <div style="margin-top:10px;">Queue: <b>{st3.queue_length}</b> / 50 units</div>
            <div class="queue-container">
                <div class="queue-fill" style="width:{fill_pct3}%; background-color:{bar_color3};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    readings = db.get_recent_readings(limit=100)
    st.plotly_chart(create_queue_chart(readings), use_container_width=True)


# 5. AI PREDICTIONS PAGE
elif st.session_state.current_page == "AI Predictions":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🧠 AI Bottleneck Risk Prediction</div>
            <div class="factory-subtitle">Random Forest Early Warning (60-Second Prediction Horizon)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    preds = db.get_recent_predictions(limit=50)
    latest_pred = preds[0] if preds else None

    col_g, col_details = st.columns([1, 1.5])
    with col_g:
        prob = latest_pred.get("risk_probability", 0.0) if latest_pred else 0.0
        st.plotly_chart(create_risk_gauge(prob), use_container_width=True)

    with col_details:
        st.markdown("#### Live Inference Breakdown")
        if latest_pred:
            is_bn = bool(latest_pred.get("bottleneck_predicted"))
            status_text = "HIGH RISK — Bottleneck Imminent" if is_bn else "NORMAL — Stable Throughput"
            badge = "<span class='badge-critical'>BOTTLENECK PREDICTED</span>" if is_bn else "<span class='badge-normal'>NORMAL</span>"
            st.markdown(f"Status: {badge}", unsafe_allow_html=True)
            st.markdown(f"- **Prediction Horizon:** 60 seconds into the future")
            st.markdown(f"- **Predicted Workstation:** `{latest_pred.get('predicted_station') or 'None'}`")
            st.markdown(f"- **Confidence Score:** {latest_pred.get('confidence', 0.0)*100:.1f}%")
            st.markdown(f"- **Model Version:** `{latest_pred.get('model_version')}`")

            feat_json = latest_pred.get("features_json")
            if feat_json:
                try:
                    fdict = json.loads(feat_json)
                    st.markdown("**Key Engineered Features Used:**")
                    st.json(fdict)
                except Exception:
                    pass
        else:
            st.info("No AI predictions recorded yet. Run simulation to trigger inference.")

    st.markdown("#### Prediction Audit Log")
    if preds:
        pred_df = pd.DataFrame(preds)[["timestamp", "horizon_sec", "bottleneck_predicted", "risk_probability", "confidence", "model_version"]]
        st.dataframe(pred_df.tail(20), use_container_width=True)


# 6. ALERTS PAGE
elif st.session_state.current_page == "Alerts":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🚨 Industrial Alert Manager</div>
            <div class="factory-subtitle">Hysteresis-Debounced Alarms and Operator Acknowledgment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    alerts = db.get_recent_alerts(limit=50)

    col_ack, col_flt = st.columns([2, 1])
    with col_flt:
        filter_sev = st.selectbox("Filter Severity", ["ALL", "CRITICAL", "WARNING", "NORMAL"])

    filtered_alerts = [a for a in alerts if filter_sev == "ALL" or a.get("severity") == filter_sev]

    st.markdown("#### Active & Recent Alerts")
    if filtered_alerts:
        for a in filtered_alerts[:10]:
            sev = a.get("severity", "WARNING")
            badge = f"<span class='badge-{sev.lower()}'>{sev}</span>"
            ack_status = f"✅ Acknowledged by {a.get('acknowledged_by')}" if a.get("acknowledged") else "⏳ Unacknowledged"
            with st.container():
                st.markdown(f"""
                <div style="background:#18202c; border-left:4px solid {'#ef4444' if sev=='CRITICAL' else ('#f59e0b' if sev=='WARNING' else '#10b981')}; padding:12px 16px; margin-bottom:8px; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{a.get('station_id')} — {a.get('alert_code')}</b>
                        {badge}
                    </div>
                    <div style="margin:4px 0; color:#e2e8f0;">{a.get('message')}</div>
                    <div style="font-size:12px; color:#94a3b8;">
                        Time: {a.get('timestamp')} | Measured: {a.get('measured_value')} | Threshold: {a.get('threshold_value')} | Status: {ack_status}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if not a.get("acknowledged"):
                    if st.button(f"Acknowledge {a.get('alert_id')[:8]}", key=a.get("alert_id")):
                        current_user = st.session_state.user["username"] if st.session_state.user else "operator"
                        db.acknowledge_alert(a.get("alert_id"), current_user)
                        st.success("Alert acknowledged.")
                        st.rerun()
    else:
        st.info("No alerts match the selected criteria.")


# 7. HISTORICAL ANALYTICS PAGE
elif st.session_state.current_page == "Historical Analytics":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">📈 Historical Analytics & CSV Export</div>
            <div class="factory-subtitle">Production Trends, Long-Term Comparisons, and Raw Data Downloads</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    readings = db.get_recent_readings(limit=300)
    line_metrics = db.get_recent_line_metrics(limit=150)

    st.plotly_chart(create_throughput_chart(line_metrics), use_container_width=True)
    st.plotly_chart(create_queue_chart(readings), use_container_width=True)

    st.markdown("#### Export Production Records")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if readings:
            csv_data = pd.DataFrame(readings).to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Station Telemetry (CSV)",
                data=csv_data,
                file_name=f"factorypulse_telemetry_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with col_e2:
        if line_metrics:
            csv_metrics = pd.DataFrame(line_metrics).to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Line Metrics (CSV)",
                data=csv_metrics,
                file_name=f"factorypulse_line_metrics_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# 8. MODEL PERFORMANCE PAGE
elif st.session_state.current_page == "Model Performance":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🎯 AI Model Performance & Metrics</div>
            <div class="factory-subtitle">Evaluation Metrics, Confusion Matrix, and Hyperparameter Specifications</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    meta = db.get_active_model_metadata()
    if meta:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{meta.get('accuracy', 0.0)*100:.1f}%")
        c2.metric("Precision", f"{meta.get('precision', 0.0)*100:.1f}%")
        c3.metric("Recall", f"{meta.get('recall', 0.0)*100:.1f}%")
        c4.metric("F1-Score", f"{meta.get('f1_score', 0.0)*100:.1f}%")

        meta_json_path = config.ML_METADATA_PATH
        if meta_json_path.exists():
            with open(meta_json_path, "r", encoding="utf-8") as f:
                full_meta = json.load(f)

            cm = full_meta.get("confusion_matrix")
            if cm:
                st.plotly_chart(create_confusion_matrix_chart(cm), use_container_width=True)

            st.markdown("#### Baseline vs Machine Learning Comparison")
            comp = full_meta.get("baseline_comparison", {})
            st.write(f"- **Baseline Rule-Based F1:** {comp.get('baseline_f1', 0.0):.4f}")
            st.write(f"- **Random Forest F1 Improvement:** +{comp.get('rf_f1_improvement', 0.0):.4f}")
            st.write(f"- **Training Samples:** {full_meta.get('train_samples')} | **Test Samples:** {full_meta.get('test_samples')}")
            st.write(f"- **Prediction Horizon:** {config.ML_PREDICTION_HORIZON_SEC} seconds into future")
    else:
        st.warning("Model metadata unavailable in database. Run train.py to train the model.")


# 9. DEVICE MANAGEMENT PAGE
elif st.session_state.current_page == "Device Management":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">🔌 ESP32 Hardware Device Management</div>
            <div class="factory-subtitle">Real Station 2 Motor Control, Optical Sensor Monitoring, and Physical Alarms</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sim = st.session_state.simulator
    c_status, c_ctrl = st.columns([1, 1.2])

    with c_status:
        st.markdown("#### Hardware Connectivity")
        is_hw = sim.station2.hardware_active
        hw_badge = "<span class='badge-normal'>ONLINE (ACTIVE)</span>" if is_hw else "<span class='badge-warning'>SIMULATED MODE</span>"
        st.markdown(f"Station 2 Operational Mode: {hw_badge}", unsafe_allow_html=True)

        st.markdown(f"""
        - **Target Device:** `esp32_station02_motor`
        - **Microcontroller:** ESP32 DevKit V1 (3.3V)
        - **IR Sensor:** LM393 Optical Slot Counter (GPIO 18)
        - **Motor Driver:** L298N Dual H-Bridge (PWM GPIO 25, Dir GPIO 26/27)
        - **Current Measured RPM:** `{sim.station2.current_rpm:.1f} RPM`
        - **Station Mode Toggle:**
        """)
        if is_hw:
            if st.button("Switch to Virtual Simulation"):
                sim.station2.hardware_active = False
                sim.station2.source = "simulated"
                st.rerun()
        else:
            if st.button("Connect to ESP32 Hardware Mode"):
                sim.station2.hardware_active = True
                sim.station2.source = "hardware"
                st.rerun()

    with c_ctrl:
        st.markdown("#### Motor Actuator Controls")
        speed_slider = st.slider("Target Motor Speed (PWM 0-255)", 0, 255, 180, 5)
        col_m1, col_m2, col_m3 = st.columns(3)

        with col_m1:
            if st.button("Apply Speed", use_container_width=True):
                cmd = {"action": "SET_SPEED", "speed_pwm": speed_slider, "timestamp": datetime.now(timezone.utc).isoformat()}
                st.session_state.mqtt_client.publish(config.TOPIC_MOTOR_COMMANDS, cmd)
                # Calibrate simulated RPM
                sim.station2.target_rpm = (speed_slider / 255.0) * config.STATION2_BASE_RPM
                st.success(f"Dispatched PWM {speed_slider}")

        with col_m2:
            if st.button("⏹️ Emergency Stop", use_container_width=True):
                cmd = {"action": "STOP", "timestamp": datetime.now(timezone.utc).isoformat()}
                st.session_state.mqtt_client.publish(config.TOPIC_MOTOR_COMMANDS, cmd)
                sim.station2.target_rpm = 0.0
                sim.station2.current_rpm = 0.0
                st.error("Emergency Stop Sent!")

        with col_m3:
            if st.button("Clear Alarm", use_container_width=True):
                cmd = {"action": "RESET_ALARM", "timestamp": datetime.now(timezone.utc).isoformat()}
                st.session_state.mqtt_client.publish(config.TOPIC_MOTOR_COMMANDS, cmd)
                st.info("Alarm Clear Sent.")


# 10. SETTINGS PAGE
elif st.session_state.current_page == "Settings":
    st.markdown("""
    <div class="factory-header">
        <div>
            <div class="factory-title">⚙️ System Configuration & Diagnostics</div>
            <div class="factory-subtitle">MQTT Broker Status, Database Parameters, and Industrial Thresholds</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    info = st.session_state.mqtt_client.connection_info
    c_mqtt, c_db = st.columns(2)

    with c_mqtt:
        st.markdown("#### MQTT Communication")
        st.write(f"- **Configured Mode:** `{config.MQTT_MODE}`")
        st.write(f"- **Runtime Mode:** `{info.get('mode')}`")
        st.write(f"- **Host:** `{info.get('host')}:{info.get('port')}`")
        st.write(f"- **Connected:** `{info.get('connected')}`")
        st.write(f"- **Messages Published:** `{info.get('messages_published')}`")
        st.write(f"- **Messages Received:** `{info.get('messages_received')}`")
        if info.get("last_error"):
            st.warning(f"Note: {info.get('last_error')}")

    with c_db:
        st.markdown("#### Database & Persistence")
        st.write(f"- **Database Path:** `{config.DATABASE_PATH}`")
        st.write(f"- **WAL Mode Enabled:** `{config.DATABASE_WAL_MODE}`")
        st.write(f"- **Connection Timeout:** `{config.DATABASE_TIMEOUT}s`")

    st.markdown("#### Industrial Alert Rule Thresholds")
    st.write(f"- **Critical RPM Ratio:** `< {config.ALERT_RPM_CRITICAL_RATIO*100:.0f}%` of nominal")
    st.write(f"- **Warning RPM Ratio:** `< {config.ALERT_RPM_WARNING_RATIO*100:.0f}%` of nominal")
    st.write(f"- **Queue Warning Limit:** `≥ {config.ALERT_QUEUE_WARNING_THRESHOLD} units`")
    st.write(f"- **Queue Critical Limit:** `≥ {config.ALERT_QUEUE_CRITICAL_THRESHOLD} units`")
    st.write(f"- **Debounce Hysteresis:** `{config.ALERT_HYSTERESIS_COUNT} consecutive cycles`")
    st.write(f"- **Alert Cooldown:** `{config.ALERT_COOLDOWN_SECONDS} seconds`")

