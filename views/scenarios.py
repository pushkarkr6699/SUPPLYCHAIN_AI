import streamlit as st
from components.section_header import section
from components.kpi_cards import kpis
from components.empty_states import empty_state
from components.navigation import nav_button
from services.mock_data import SHIPPING, SCENARIO_DEMAND_BASE
from services.scenario_service import delivery_scenario, demand_scenario


def reset_scenario():
    st.session_state["scenario_shipping_select"] = SHIPPING[0]
    st.session_state["scenario_multiplier"] = 1.0


def render(df):
    st.html('<div class="simulation-banner"><span class="simulation-dot"></span><div><b>MODEL-BASED SIMULATION</b><small>Illustrative demo rules · no production model is executed · simulated outputs are not causal effects</small></div></div>')
    delivery, demand, profitability = st.tabs(["Delivery Scenario", "Demand Scenario", "Profitability"])
    scenario_summaries = []
    with delivery:
        controls, result = st.columns([1, 1.7], gap="large")
        with controls, st.container(border=True):
            section("Scenario Controls", "Choose a baseline record and supported input")
            baseline_id = st.selectbox("Baseline order", df.Order.tolist(), key="scenario_baseline")
            row = df[df.Order.eq(baseline_id)].iloc[0]
            shipping = st.selectbox("Scenario shipping mode", SHIPPING, index=SHIPPING.index(row["Shipping Mode"]), key="scenario_shipping_select")
        scenario = delivery_scenario(row["Risk Probability"], row["Shipping Mode"], shipping)
        scenario_summaries.append({"Type": "Delivery", "Baseline": float(row["Risk Probability"]), "Scenario": float(scenario)})
        with result, st.container(border=True):
            section("Baseline vs Scenario", "Illustrative delivery probability adjustment")
            st.progress(float(row["Risk Probability"]), text=f'Baseline · {row["Risk Probability"]:.1%}')
            st.progress(float(scenario), text=f"Scenario · {scenario:.1%}")
            kpis([
                ("Baseline Risk", row["Risk Probability"], "percent", f'{row["Order"]} · demo baseline'),
                ("Scenario Risk", scenario, "percent", "Illustrative rule output", "purple"),
                ("Probability Change", (scenario - row["Risk Probability"]) * 100, "decimal", "Percentage points"),
            ])
            st.caption("The scenario is isolated from the source record and production threshold.")
    with demand:
        controls, result = st.columns([1, 1.7], gap="large")
        with controls, st.container(border=True):
            section("Demand Controls", "Adjust the supported demo planning multiplier")
            multiplier = st.slider("Demand multiplier", .5, 1.5, 1., .05, key="scenario_multiplier")
        forecast = demand_scenario(multiplier)
        scenario_summaries.append({"Type": "Demand", "Baseline": float(SCENARIO_DEMAND_BASE), "Scenario": float(forecast)})
        with result, st.container(border=True):
            section("Baseline vs Scenario", "Illustrative demand units")
            kpis([
                ("Baseline Forecast", SCENARIO_DEMAND_BASE, "number", "Mock-service fixture"),
                ("Scenario Forecast", forecast, "number", "Illustrative units", "purple"),
                ("Demand Change", forecast - SCENARIO_DEMAND_BASE, "number", "Scenario minus baseline"),
            ])
            band_col, _ = st.columns([1, 2])
            band_col.metric("Scenario band", "Higher" if multiplier > 1.1 else "Lower" if multiplier < .9 else "Typical")
    with profitability:
        empty_state("Profitability scenarios are unavailable", "Connect a verified profitability model and supported feature schema before simulation.", "Model Not Connected")
    actions = st.columns([1, 1, 1, 4])
    actions[0].button("Reset Scenario", on_click=reset_scenario, key="scenario_reset")
    if actions[1].button("Save Scenario", key="scenario_save"):
        saved = st.session_state.get("saved_scenarios", [])
        saved.extend(scenario_summaries)
        st.session_state.saved_scenarios = saved[-10:]
        st.toast("Scenario saved for this session.")
    with actions[2]: nav_button("Ask Copilot", "copilot", key="scenario_copilot")
    if st.session_state.get("saved_scenarios"):
        with st.expander("Saved scenarios · session only"):
            st.dataframe(st.session_state.saved_scenarios, hide_index=True, width="stretch")
