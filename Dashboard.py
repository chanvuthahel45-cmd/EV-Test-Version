import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import random
import time

# ==================================================
# PAGE CONFIGURATION - ORIGINAL CLEAN DESIGN
# ==================================================

st.set_page_config(
    page_title="EV Load Simulator",
    page_icon="⚡",
    layout="wide"
)

# Original clean CSS
st.markdown("""
<style>
    /* Clean, simple styling */
    .main {
        background: #f0f2f6;
    }

    /* Simple card */
    .card {
        background: white;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }

    /* Simple metric */
    .metric-box {
        background: white;
        border-radius: 6px;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        text-align: center;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a1a2e;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    /* Sidebar */
    .css-1d391kg {
        background: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #1a1a2e;
    }

    /* Buttons */
    .stButton > button {
        background: #1a1a2e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #2d2d44;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    /* Divider */
    .divider {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }

    /* Info box */
    .info-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #1a1a2e;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #e0e0e0;
        margin-top: 2rem;
    }

    /* Dataframe */
    .dataframe {
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: #1a1a2e;
        border-radius: 4px;
    }

    /* Status indicators */
    .status-ok { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-danger { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# DATA
# ==================================================

CAR_MODELS = {
    "BYD Atto 3": {"battery": 60.5, "max_charge_rate": 11.0, "category": "SUV"},
    "Mazda EZ-60": {"battery": 68.8, "max_charge_rate": 11.0, "category": "SUV"},
    "Tesla Model 3": {"battery": 60.0, "max_charge_rate": 11.0, "category": "Sedan"},
    "Tesla Model Y": {"battery": 75.0, "max_charge_rate": 11.0, "category": "SUV"},
    "Nissan Leaf": {"battery": 40.0, "max_charge_rate": 6.6, "category": "Hatchback"},
    "BYD Dolphin": {"battery": 44.9, "max_charge_rate": 7.0, "category": "Hatchback"},
    "Kia EV6": {"battery": 77.4, "max_charge_rate": 11.0, "category": "SUV"},
    "Hyundai Ioniq 5": {"battery": 72.6, "max_charge_rate": 11.0, "category": "SUV"},
    "MG ZS EV": {"battery": 50.3, "max_charge_rate": 7.0, "category": "SUV"},
    "Wuling Air EV": {"battery": 26.7, "max_charge_rate": 3.3, "category": "Compact"},
    "Custom": {"battery": 50.0, "max_charge_rate": 7.0, "category": "Custom"}
}

CHARGING_TYPES = {
    "Level 1": {"power": 1.8, "range": (1.4, 2.4), "icon": "🔌"},
    "Level 2": {"power": 7.0, "range": (3.3, 11.0), "icon": "⚡"},
    "DC Fast": {"power": 50.0, "range": (25.0, 150.0), "icon": "🚀"}
}

SCENARIOS = {
    "Residential": {
        "arrival": 20, "arrival_std": 2,
        "soc": 60, "soc_std": 20,
        "icon": "🏠",
        "color": "#3B82F6",
        "description": "Evening charging at home"
    },
    "Office": {
        "arrival": 9, "arrival_std": 1.5,
        "soc": 70, "soc_std": 15,
        "icon": "🏢",
        "color": "#10B981",
        "description": "Daytime workplace charging"
    },
    "Public": {
        "arrival": 12, "arrival_std": 6,
        "soc": 30, "soc_std": 15,
        "icon": "📍",
        "color": "#F59E0B",
        "description": "Opportunistic public charging"
    },
    "Mixed": {
        "arrival": None, "arrival_std": None,
        "soc": None, "soc_std": None,
        "icon": "🔄",
        "color": "#8B5CF6",
        "description": "Combined: Residential + Office + Public"
    }
}


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def get_car_specs(model):
    if model in CAR_MODELS:
        return CAR_MODELS[model]
    return CAR_MODELS["Custom"]


def generate_ev(config):
    scenario = config["scenario"]
    model = config["model"]
    charge_type = config["charge_type"]

    if scenario == "Mixed":
        sub_scenarios = ["Residential", "Office", "Public"]
        weights = [config.get("res_weight", 0.4),
                   config.get("off_weight", 0.35),
                   config.get("pub_weight", 0.25)]
        scenario = np.random.choice(sub_scenarios, p=weights)
        sc_config = SCENARIOS[scenario]
    else:
        sc_config = SCENARIOS[scenario]

    arrival = np.clip(
        np.random.normal(sc_config["arrival"], sc_config["arrival_std"]),
        0, 23
    )

    soc = np.clip(
        np.random.normal(sc_config["soc"], sc_config["soc_std"]),
        10, 100
    )

    specs = get_car_specs(model)
    battery = specs["battery"] * np.random.uniform(0.95, 1.05)
    max_rate = specs["max_charge_rate"] * np.random.uniform(0.90, 1.10)

    if charge_type in CHARGING_TYPES:
        ct_config = CHARGING_TYPES[charge_type]
        power = np.random.uniform(ct_config["range"][0], ct_config["range"][1])
    else:
        power = 7.0

    energy_needed = battery * (100 - soc) / 100
    charge_rate = min(power, max_rate)
    duration = energy_needed / charge_rate if charge_rate > 0 else 0

    return {
        "scenario": scenario,
        "model": model,
        "arrival": arrival,
        "soc": soc,
        "battery": battery,
        "charge_type": charge_type,
        "charge_rate": charge_rate,
        "duration": duration,
        "energy": energy_needed
    }


def run_simulation(config_list, iterations=1000):
    all_profiles = []
    last_evs = None

    for i in range(iterations):
        hourly = np.zeros(24)
        evs = []

        for config in config_list:
            count = config["count"]
            for _ in range(count):
                ev = generate_ev(config)
                evs.append(ev)

                start = int(ev["arrival"])
                for h in range(int(np.ceil(ev["duration"]))):
                    hourly[(start + h) % 24] += ev["charge_rate"]

        all_profiles.append(hourly)
        if i == iterations - 1:
            last_evs = evs

    return np.array(all_profiles), last_evs


# ==================================================
# SIDEBAR - ORIGINAL STYLE
# ==================================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # Scenario Selection
    scenario = st.selectbox(
        "Scenario",
        ["Residential", "Office", "Public", "Mixed"],
        format_func=lambda x: f"{SCENARIOS[x]['icon']} {x}"
    )
    st.caption(SCENARIOS[scenario]["description"])

    st.markdown("---")

    # EV Configuration
    st.markdown("### 🚗 EV Configuration")

    if 'fleet_configs' not in st.session_state:
        if scenario == "Mixed":
            st.session_state.fleet_configs = [
                {"scenario": "Mixed", "model": "BYD Atto 3", "count": 40, "charge_type": "Level 2",
                 "res_weight": 0.4, "off_weight": 0.35, "pub_weight": 0.25},
                {"scenario": "Mixed", "model": "Tesla Model 3", "count": 30, "charge_type": "DC Fast",
                 "res_weight": 0.4, "off_weight": 0.35, "pub_weight": 0.25},
                {"scenario": "Mixed", "model": "Nissan Leaf", "count": 20, "charge_type": "Level 2",
                 "res_weight": 0.4, "off_weight": 0.35, "pub_weight": 0.25}
            ]
        else:
            st.session_state.fleet_configs = [
                {"scenario": scenario, "model": "BYD Atto 3", "count": 50, "charge_type": "Level 2"}
            ]

    total_evs = 0
    for idx, config in enumerate(st.session_state.fleet_configs):
        with st.container():
            st.markdown(f"**Group {idx + 1}**")

            cols = st.columns([2, 1.5, 1.2, 0.5])

            with cols[0]:
                model = st.selectbox(
                    "Model",
                    list(CAR_MODELS.keys()),
                    index=list(CAR_MODELS.keys()).index(config["model"]) if config["model"] in CAR_MODELS else 0,
                    key=f"model_{idx}",
                    label_visibility="collapsed"
                )
                specs = get_car_specs(model)
                st.caption(f"{specs['battery']:.0f} kWh | {specs['max_charge_rate']:.0f} kW")

            with cols[1]:
                charge_type = st.selectbox(
                    "Charge",
                    ["Level 1", "Level 2", "DC Fast"],
                    key=f"charge_{idx}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                count = st.number_input(
                    "Qty",
                    min_value=1,
                    max_value=500,
                    value=config["count"],
                    key=f"count_{idx}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                if len(st.session_state.fleet_configs) > 1:
                    if st.button("✕", key=f"remove_{idx}"):
                        st.session_state.fleet_configs.pop(idx)
                        st.rerun()

            st.session_state.fleet_configs[idx]["model"] = model
            st.session_state.fleet_configs[idx]["count"] = count
            st.session_state.fleet_configs[idx]["charge_type"] = charge_type

            total_evs += count

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("➕ Add Model", use_container_width=True):
            if scenario == "Mixed":
                st.session_state.fleet_configs.append(
                    {"scenario": "Mixed", "model": "Tesla Model 3", "count": 10, "charge_type": "Level 2",
                     "res_weight": 0.4, "off_weight": 0.35, "pub_weight": 0.25}
                )
            else:
                st.session_state.fleet_configs.append(
                    {"scenario": scenario, "model": "Tesla Model 3", "count": 10, "charge_type": "Level 2"}
                )
            st.rerun()

    st.caption(f"**Total EVs:** {total_evs}")

    st.markdown("---")

    # Simulation Parameters
    st.markdown("### ⚙️ Simulation")

    transformer_kva = st.number_input("Transformer (kVA)", 100, 5000, 1000, 100)
    iterations = st.slider("Monte Carlo Iterations", 100, 10000, 1000, 100)

    if iterations >= 5000:
        st.success("✅ High confidence")
    elif iterations >= 1000:
        st.info("ℹ️ Good confidence")
    else:
        st.warning("⚠️ Lower confidence")

    st.markdown("---")

    # Fleet Summary
    if st.session_state.fleet_configs:
        summary_data = []
        for cfg in st.session_state.fleet_configs:
            specs = get_car_specs(cfg["model"])
            summary_data.append({
                "Model": cfg["model"][:12] + ".." if len(cfg["model"]) > 12 else cfg["model"],
                "Qty": cfg["count"],
                "Charge": cfg["charge_type"]
            })
        st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    st.markdown("---")

    run = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

# ==================================================
# MAIN CONTENT
# ==================================================

st.title("⚡ EV Load Impact Simulator")
st.caption("Monte Carlo Simulation | EV Charging Impact on Power Grid")

if run:
    if not st.session_state.fleet_configs:
        st.warning("⚠️ Please add at least one EV model configuration.")
    else:
        with st.spinner(f"Running {iterations:,} Monte Carlo iterations..."):
            start_time = time.time()

            configs = []
            for cfg in st.session_state.fleet_configs:
                configs.append({
                    "scenario": cfg["scenario"],
                    "model": cfg["model"],
                    "count": cfg["count"],
                    "charge_type": cfg["charge_type"],
                    "res_weight": cfg.get("res_weight", 0.4),
                    "off_weight": cfg.get("off_weight", 0.35),
                    "pub_weight": cfg.get("pub_weight", 0.25)
                })

            profiles, last_evs = run_simulation(configs, iterations)

            mean_load = np.mean(profiles, axis=0)
            std_load = np.std(profiles, axis=0)
            lower = np.percentile(profiles, 5, axis=0)
            upper = np.percentile(profiles, 95, axis=0)

            peak_load = np.max(mean_load)
            peak_hour = np.argmax(mean_load)
            total_energy = np.sum(mean_load)
            avg_load = np.mean(mean_load)
            load_factor = avg_load / peak_load if peak_load > 0 else 0

            transformer_kw = transformer_kva * 0.9
            utilization = peak_load / transformer_kw if transformer_kw > 0 else 0

            model_counts = {}
            model_energy = {}
            charge_counts = {}
            charge_energy = {}

            for ev in last_evs:
                model = ev["model"]
                model_counts[model] = model_counts.get(model, 0) + 1
                model_energy[model] = model_energy.get(model, 0) + ev["energy"]

                ct = ev["charge_type"]
                charge_counts[ct] = charge_counts.get(ct, 0) + 1
                charge_energy[ct] = charge_energy.get(ct, 0) + ev["energy"]

            end_time = time.time()
            sim_time = end_time - start_time

# ==================================================
# RESULTS
# ==================================================

if run and st.session_state.fleet_configs:
    scenario_color = SCENARIOS[scenario]["color"]
    scenario_icon = SCENARIOS[scenario]["icon"]

    st.markdown(f"### {scenario_icon} {scenario} Scenario Results")
    st.caption(f"{iterations:,} iterations · {total_evs:,} EVs · {sim_time:.1f}s")

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🚗 EVs", f"{total_evs:,}")
    col2.metric("⚡ Peak Load", f"{peak_load:.0f} kW", f"Hour {peak_hour:.0f}:00")
    col3.metric("🔋 Total Energy", f"{total_energy:.0f} kWh")
    col4.metric("📊 Load Factor", f"{load_factor:.1%}")
    col5.metric("🏭 Transformer", f"{utilization:.0%}",
                "⚠️ Overload" if utilization > 1 else "✅ OK" if utilization < 0.8 else "🟡 High")

    st.divider()

    # Load Profile Chart
    hours = np.arange(24)

    fig = go.Figure()

    # Confidence bands
    fig.add_trace(go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([upper, lower[::-1]]),
        fill='toself',
        fillcolor=f'rgba(26, 26, 46, 0.1)',
        line=dict(width=0),
        name='95% Confidence'
    ))

    fig.add_trace(go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([mean_load + std_load, (mean_load - std_load)[::-1]]),
        fill='toself',
        fillcolor=f'rgba(26, 26, 46, 0.08)',
        line=dict(width=0),
        name='±1σ'
    ))

    fig.add_trace(go.Scatter(
        x=hours,
        y=mean_load,
        mode='lines+markers',
        name='Total Load',
        line=dict(color='#1a1a2e', width=2.5),
        marker=dict(size=6, color='#1a1a2e')
    ))

    # Transformer limit
    fig.add_hline(
        y=transformer_kw,
        line_dash="dash",
        line_color="#dc3545",
        annotation_text=f"Limit: {transformer_kw:.0f} kW"
    )

    fig.update_layout(
        title=f"24-Hour Load Profile - {scenario} Scenario",
        xaxis_title="Hour of Day",
        yaxis_title="Load (kW)",
        height=500,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Analysis Section
    st.subheader("📊 Detailed Analysis")

    col1, col2 = st.columns(2)

    with col1:
        if model_counts:
            fig_models = go.Figure(data=[go.Pie(
                labels=list(model_counts.keys()),
                values=list(model_counts.values()),
                hole=0.3,
                textinfo="label+percent",
                marker=dict(colors=['#1a1a2e', '#2d2d44', '#495057', '#6c757d', '#adb5bd'])
            )])
            fig_models.update_layout(
                title="EV Models by Count",
                height=350,
                template="plotly_white"
            )
            st.plotly_chart(fig_models, use_container_width=True)

    with col2:
        if charge_counts:
            fig_charge = go.Figure(data=[go.Pie(
                labels=list(charge_counts.keys()),
                values=list(charge_counts.values()),
                hole=0.3,
                textinfo="label+percent",
                marker=dict(colors=['#6c757d', '#495057', '#1a1a2e'])
            )])
            fig_charge.update_layout(
                title="Charging Types",
                height=350,
                template="plotly_white"
            )
            st.plotly_chart(fig_charge, use_container_width=True)

    # Export
    st.divider()
    st.subheader("📥 Export Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_load = pd.DataFrame({
            "Hour": hours,
            "Mean_kW": mean_load,
            "Std_kW": std_load,
            "Lower_5%": lower,
            "Upper_95%": upper
        }).to_csv(index=False).encode()
        st.download_button("📊 Load Profile", csv_load, "load_profile.csv", "text/csv")

    with col2:
        if last_evs:
            df_ev = pd.DataFrame(last_evs)
            csv_ev = df_ev.to_csv(index=False).encode()
            st.download_button("🚗 EV Data", csv_ev, "ev_data.csv", "text/csv")

    with col3:
        summary_data = []
        for cfg in st.session_state.fleet_configs:
            specs = get_car_specs(cfg["model"])
            summary_data.append({
                "Model": cfg["model"],
                "Count": cfg["count"],
                "Charger": cfg["charge_type"]
            })
        csv_summary = pd.DataFrame(summary_data).to_csv(index=False).encode()
        st.download_button("📋 Fleet Summary", csv_summary, "fleet_summary.csv", "text/csv")

else:
    # Welcome - Original style with scenario comparison
    st.info("👈 Configure your simulation in the sidebar and click 'Run Simulation'")

    st.subheader("📊 Scenario Comparison")

    comp_data = []
    for name, config in SCENARIOS.items():
        if name != "Mixed":
            comp_data.append({
                "Scenario": f"{config['icon']} {name}",
                "Peak Time": f"{config['arrival']:02d}:00 ±{config['arrival_std']}h",
                "Typical SOC": f"{config['soc']}% ±{config['soc_std']}%",
                "Use Case": config['description']
            })
        else:
            comp_data.append({
                "Scenario": f"{config['icon']} {name}",
                "Peak Time": "Multiple peaks",
                "Typical SOC": "Mixed distribution",
                "Use Case": config['description']
            })

    st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

    with st.expander("📖 How Mixed Scenario Works"):
        st.markdown("""
        **Mixed Scenario Logic:**

        1. **Residential (40% default):** 
           - Evening arrivals (20:00 ± 2h)
           - Higher SOC (60% ± 20%)
           - Home charging pattern

        2. **Office (35% default):**
           - Morning arrivals (9:00 ± 1.5h)
           - Highest SOC (70% ± 15%)
           - Workplace charging pattern

        3. **Public (25% default):**
           - Distributed arrivals (12:00 ± 6h)
           - Lowest SOC (30% ± 15%)
           - Opportunistic charging

        **The simulation:**
        - Randomly assigns each EV to a scenario based on weights
        - Uses scenario-specific arrival and SOC distributions
        - Aggregates all loads into total profile
        - Shows individual scenario contributions in results
        """)

# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="footer">
    ⚡ EV Load Simulator · Monte Carlo Simulation Engine
</div>
""", unsafe_allow_html=True)