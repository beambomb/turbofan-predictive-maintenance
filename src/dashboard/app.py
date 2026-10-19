from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "features_fd001.parquet"
MODEL_PATH = BASE_DIR / "models" / "best_rul_model.joblib"

FEATURE_COLUMNS = [
    "setting_1", "setting_2", "setting_3",
    "sensor_2_lpc_temp", "sensor_3_hpc_temp", "sensor_4_lpt_temp",
    "sensor_7_hpc_pressure", "sensor_8_fan_speed", "sensor_9_core_speed",
    "sensor_11_static_hpc_pressure", "sensor_12_fuel_flow_ratio",
    "sensor_13_corrected_fan_speed", "sensor_14_corrected_core_speed",
    "sensor_15_bypass_ratio", "sensor_17_bleed_enthalpy",
    "sensor_20_hpt_coolant_bleed", "sensor_21_lpt_coolant_bleed",
    "s2_drift_initial", "s3_drift_initial", "s4_drift_initial",
    "s7_drift_initial", "s11_drift_initial", "s12_drift_initial",
    "s2_roll_mean_5", "s3_roll_mean_5", "s4_roll_mean_5",
    "s7_roll_mean_5", "s8_roll_mean_5", "s9_roll_mean_5",
    "s11_roll_mean_5", "s12_roll_mean_5", "s15_roll_mean_5",
    "s2_roll_std_5", "s3_roll_std_5", "s4_roll_std_5",
    "s7_roll_std_5", "s11_roll_std_5", "s12_roll_std_5"
]

st.set_page_config(
    page_title="NASA Turbofan Fleet Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
    }
    .metric-card {
        background: rgba(18, 24, 38, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .status-healthy {
        color: #10b981;
        font-weight: 700;
    }
    .status-warning {
        color: #f59e0b;
        font-weight: 700;
    }
    .status-critical {
        color: #ef4444;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH)
    return df


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


df = load_data()
model = load_model()

if "pred_rul" not in df.columns:
    df["pred_rul"] = np.clip(model.predict(df[FEATURE_COLUMNS]), 0.0, 125.0)

latest_fleet_df = df.sort_values("cycle").groupby("engine_id").last().reset_index()


def classify_health(rul):
    if rul > 75.0:
        return "HEALTHY"
    elif 25.0 <= rul <= 75.0:
        return "WARNING"
    else:
        return "CRITICAL"


latest_fleet_df["health_status"] = latest_fleet_df["pred_rul"].apply(classify_health)

total_engines = len(latest_fleet_df)
healthy_count = (latest_fleet_df["health_status"] == "HEALTHY").sum()
warning_count = (latest_fleet_df["health_status"] == "WARNING").sum()
critical_count = (latest_fleet_df["health_status"] == "CRITICAL").sum()

st.title("NASA Turbofan Fleet Intelligence Platform")
st.markdown("Real-time aircraft fleet health monitoring, remaining useful life predictions, and decision intelligence")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Monitored Fleet", f"{total_engines} Engines")
with col2:
    st.metric("Healthy Status", f"{healthy_count} Engines", delta="Normal", delta_color="normal")
with col3:
    st.metric("Warning Status", f"{warning_count} Engines", delta="Needs Inspection", delta_color="off")
with col4:
    st.metric("Critical Status", f"{critical_count} Engines", delta="Urgent Action", delta_color="inverse")

tab1, tab2, tab3 = st.tabs([
    "Fleet Health Overview",
    "Engine Telemetry and Degradation Analysis",
    "Decision Intelligence and Maintenance Cost Simulator"
])

with tab1:
    st.subheader("Fleet Risk and Health Distribution")
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        status_counts = latest_fleet_df["health_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {"HEALTHY": "#10b981", "WARNING": "#f59e0b", "CRITICAL": "#ef4444"}
        fig_donut = px.pie(
            status_counts,
            values="Count",
            names="Status",
            hole=0.55,
            color="Status",
            color_discrete_map=color_map,
            title="Fleet Status Breakdown"
        )
        fig_donut.update_layout(template="plotly_dark", margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        fig_hist = px.histogram(
            latest_fleet_df,
            x="pred_rul",
            nbins=25,
            color="health_status",
            color_discrete_map=color_map,
            title="Predicted RUL Distribution Across Fleet"
        )
        fig_hist.update_layout(
            template="plotly_dark",
            xaxis_title="Predicted Remaining Useful Life Cycles",
            yaxis_title="Engine Count",
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("High Risk Engines Needing Immediate Inspection")
    ranked_fleet = latest_fleet_df[[
        "engine_id", "cycle", "pred_rul", "target_rul", "health_status",
        "sensor_2_lpc_temp", "sensor_3_hpc_temp", "sensor_7_hpc_pressure"
    ]].sort_values("pred_rul", ascending=True)

    ranked_fleet.columns = [
        "Engine ID", "Current Cycle", "Predicted RUL", "Ground Truth RUL", "Status",
        "LPC Temp R", "HPC Temp R", "HPC Pressure psia"
    ]

    st.dataframe(
        ranked_fleet.head(15).style.format({
            "Predicted RUL": "{:.1f}",
            "Ground Truth RUL": "{:.1f}",
            "LPC Temp R": "{:.2f}",
            "HPC Temp R": "{:.2f}",
            "HPC Pressure psia": "{:.2f}"
        }),
        use_container_width=True
    )

with tab2:
    st.subheader("Single Engine Telemetry and Degradation Inspection")
    selected_engine = st.selectbox("Select Target Engine ID", options=sorted(df["engine_id"].unique()), index=0)

    engine_data = df[df["engine_id"] == selected_engine].sort_values("cycle")
    max_c = engine_data["cycle"].max()
    curr_rul = engine_data["pred_rul"].iloc[-1]
    curr_status = classify_health(curr_rul)

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.info(f"Total Observed Cycles: **{max_c}**")
    with stat_col2:
        st.metric("Latest Predicted RUL", f"{curr_rul:.1f} Cycles")
    with stat_col3:
        if curr_status == "HEALTHY":
            st.success("Health State: HEALTHY")
        elif curr_status == "WARNING":
            st.warning("Health State: WARNING")
        else:
            st.error("Health State: CRITICAL")

    st.markdown("### Predicted RUL vs Ground Truth Target RUL")
    fig_rul = go.Figure()
    fig_rul.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["target_rul"],
        mode="lines",
        name="Actual Ground Truth RUL",
        line=dict(color="#94a3b8", width=2, dash="dash")
    ))
    fig_rul.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["pred_rul"],
        mode="lines",
        name="Tuned XGBoost Prediction",
        line=dict(color="#38bdf8", width=3)
    ))
    fig_rul.add_hline(y=75, line_dash="dot", line_color="#f59e0b", annotation_text="Warning Threshold 75 Cycles")
    fig_rul.add_hline(y=25, line_dash="dot", line_color="#ef4444", annotation_text="Critical Threshold 25 Cycles")
    fig_rul.update_layout(
        template="plotly_dark",
        xaxis_title="Flight Cycle",
        yaxis_title="Remaining Useful Life Cycles",
        hovermode="x unified",
        margin=dict(t=30, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_rul, use_container_width=True)

    st.markdown("### Thermal Degradation: LPC and HPC Temperatures")
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["sensor_2_lpc_temp"],
        name="LPC Outlet Temp T24",
        line=dict(color="#fb923c", width=2)
    ))
    fig_temp.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["sensor_3_hpc_temp"],
        name="HPC Outlet Temp T30",
        line=dict(color="#f43f5e", width=2),
        yaxis="y2"
    ))
    fig_temp.update_layout(
        template="plotly_dark",
        xaxis_title="Flight Cycle",
        yaxis_title="LPC Temp Deg R",
        yaxis2=dict(
            title="HPC Temp Deg R",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        margin=dict(t=30, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    st.markdown("### Mechanical Degradation: Pressures and Rotational Speeds")
    fig_mech = go.Figure()
    fig_mech.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["sensor_7_hpc_pressure"],
        name="HPC Pressure P30 psia",
        line=dict(color="#06b6d4", width=2)
    ))
    fig_mech.add_trace(go.Scatter(
        x=engine_data["cycle"],
        y=engine_data["sensor_9_core_speed"],
        name="Core Speed rpm",
        line=dict(color="#a855f7", width=2),
        yaxis="y2"
    ))
    fig_mech.update_layout(
        template="plotly_dark",
        xaxis_title="Flight Cycle",
        yaxis_title="HPC Pressure psia",
        yaxis2=dict(
            title="Core Speed rpm",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        margin=dict(t=30, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_mech, use_container_width=True)

with tab3:
    st.subheader("Decision Intelligence and Maintenance Cost Simulator")
    st.markdown("Compare airline financial expenditure across reactive, periodic, and predictive maintenance strategies")

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        cost_breakdown = st.slider(
            "Unscheduled Breakdown Cost USD",
            min_value=50000,
            max_value=300000,
            value=150000,
            step=10000
        )
    with sim_col2:
        cost_inspection = st.slider(
            "Depot Inspection Cost USD",
            min_value=5000,
            max_value=50000,
            value=15000,
            step=2500
        )
    with sim_col3:
        alert_threshold = st.slider(
            "RUL Maintenance Alert Threshold Cycles",
            min_value=10,
            max_value=50,
            value=25,
            step=5
        )

    val_engines = df["engine_id"].unique()[80:]
    val_df = df[df["engine_id"].isin(val_engines)].copy()

    cost_reactive = len(val_engines) * cost_breakdown

    cost_periodic = 0
    for eng in val_engines:
        eng_df = val_df[val_df["engine_id"] == eng]
        m_c = eng_df["cycle"].max()
        inspections = m_c // 100
        cost_periodic += inspections * cost_inspection

    cost_pdm = 0
    caught_count = 0
    for eng in val_engines:
        eng_df = val_df[val_df["engine_id"] == eng].sort_values("cycle")
        triggered = eng_df[eng_df["pred_rul"] <= alert_threshold]
        if not triggered.empty:
            cost_pdm += cost_inspection
            caught_count += 1
        else:
            cost_pdm += cost_breakdown

    savings_vs_reactive = cost_reactive - cost_pdm
    savings_vs_periodic = cost_periodic - cost_pdm
    pct_saved_periodic = (savings_vs_periodic / cost_periodic) * 100 if cost_periodic > 0 else 0

    metric_c1, metric_c2, metric_c3 = st.columns(3)
    with metric_c1:
        st.metric("Reactive Failure Policy Cost", f"${cost_reactive:,.0f}")
    with metric_c2:
        st.metric("Fixed Periodic Policy Cost", f"${cost_periodic:,.0f}")
    with metric_c3:
        st.metric("Predictive Maintenance Cost", f"${cost_pdm:,.0f}", delta=f"${savings_vs_periodic:,.0f} Saved vs Periodic")

    st.markdown("### Cost Strategy Breakdown")
    cost_summary_df = pd.DataFrame({
        "Policy": ["Reactive Run to Failure", "Periodic Every 100 Cycles", "Predictive Maintenance XGBoost"],
        "Total Cost USD": [cost_reactive, cost_periodic, cost_pdm]
    })

    fig_cost = px.bar(
        cost_summary_df,
        x="Policy",
        y="Total Cost USD",
        color="Policy",
        color_discrete_sequence=["#ef4444", "#f59e0b", "#10b981"],
        text_auto="$,.0f"
    )
    fig_cost.update_layout(
        template="plotly_dark",
        yaxis_title="Expenditure USD",
        xaxis_title="",
        showlegend=False,
        margin=dict(t=30, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_cost, use_container_width=True)

    st.markdown("### Alert Threshold Sensitivity Curve")
    threshold_tests = list(range(10, 65, 5))
    threshold_costs = []
    for th in threshold_tests:
        th_cost = 0
        for eng in val_engines:
            eng_df = val_df[val_df["engine_id"] == eng].sort_values("cycle")
            trig = eng_df[eng_df["pred_rul"] <= th]
            if not trig.empty:
                th_cost += cost_inspection
            else:
                th_cost += cost_breakdown
        threshold_costs.append(th_cost)

    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=threshold_tests,
        y=threshold_costs,
        mode="lines+markers",
        line=dict(color="#10b981", width=3),
        marker=dict(size=8, color="#34d399")
    ))
    fig_sens.add_vline(x=alert_threshold, line_dash="dash", line_color="#38bdf8", annotation_text=f"Selected Threshold: {alert_threshold}")
    fig_sens.update_layout(
        template="plotly_dark",
        xaxis_title="Remaining Useful Life Threshold Cycles",
        yaxis_title="Estimated Fleet Maintenance Cost USD",
        margin=dict(t=30, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_sens, use_container_width=True)
