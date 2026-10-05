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
    if df.attrs.get("verified_artifacts"):
        _render_verified(df)
        return
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


def _render_verified(df):
    from services.inference_service import status, input_rows, predict_delivery
    availability = status()
    section("Delivery Prediction Lab", "Run the registered trained model on an order and compare a shipping input")
    st.caption("Input changes produce model estimates, not measured causal effects. Source records and the decision threshold remain unchanged.")
    if not availability.get("available"):
        st.warning(availability.get("reason", "The trained model is not ready for inference."))
    if df.empty:
        st.info("Select a filter range containing delivery orders.")
        return
    with st.form("verified_prediction_form"):
        orders = df.Order.drop_duplicates().tolist()
        selected = st.session_state.get("selected_order")
        order = st.selectbox("Baseline order", orders, index=orders.index(selected) if selected in orders else 0)
        shipping = st.selectbox("Compare shipping mode", sorted(df["Shipping Mode"].dropna().unique().tolist()))
        submitted = st.form_submit_button("Run trained model", disabled=not availability.get("available"))
    if submitted:
        try:
            with st.spinner("Running the registered trained model…", show_time=True):
                baseline = input_rows([order])
                alternative = baseline.copy()
                alternative["Shipping Mode"] = shipping
                original = predict_delivery(baseline).iloc[0]
                changed = predict_delivery(alternative).iloc[0]
            result = {"Order": order, "Shipping Mode": shipping, "Baseline Risk": float(original["Risk Probability"]), "Scenario Risk": float(changed["Risk Probability"])}
            st.session_state.verified_prediction_result = result
            st.success("Trained prediction complete. Source records remain unchanged.")
        except (ValueError, RuntimeError, OSError) as error:
            st.error(str(error))
    result = st.session_state.get("verified_prediction_result")
    if result:
        st.caption(f'Order {result["Order"]} · compared shipping: {result["Shipping Mode"]}')
        kpis([
            ("Baseline Risk", result["Baseline Risk"], "percent", "Trained model inference"),
            ("Compared Risk", result["Scenario Risk"], "percent", "Changed shipping input", "purple"),
            ("Difference", 100 * (result["Scenario Risk"] - result["Baseline Risk"]), "decimal", "Percentage points"),
        ])
    with st.expander("Score order-level feature rows from CSV"):
        from services.inference_service import FEATURES
        st.caption("Provide the trained order-level features with their original column names. These estimates are separate from supplied historical scores.")
        st.code(", ".join(FEATURES), language="text")
        uploaded = st.file_uploader("Order features CSV", type=["csv"], key="delivery_features_upload")
        if uploaded is not None and st.button("Score uploaded orders", disabled=not availability.get("available")):
            try:
                import pandas as pd
                from services.export_service import csv_bytes
                scored = predict_delivery(pd.read_csv(uploaded))
                st.dataframe(scored, hide_index=True, width="stretch")
                st.download_button("Download trained order predictions", csv_bytes(scored), "trained_order_predictions.csv", "text/csv")
            except Exception as exc:
                st.error(f"Order inputs could not be validated: {exc}")
    st.caption("Open Demand Intelligence to run next-day web-visit predictions from daily history.")
