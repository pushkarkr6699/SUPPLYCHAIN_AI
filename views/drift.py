import pandas as pd
import streamlit as st
from components.empty_states import empty_state, disabled_panels
from components.kpi_cards import kpis
from components.status import badge
from components.section_header import section


def render(df):
    st.html('<div class="model-meta-row">' + badge("Reference Window", "neutral") + " " + badge("Current Window", "neutral") + " " + badge("Drift Status · Unavailable", "warning") + '<span>Comparable production distributions are not connected</span></div>')
    kpis([
        ("Reference Records", "Not connected", "number", "No baseline window"),
        ("Current Records", "Not connected", "number", "No production window"),
        ("Features Monitored", "Not configured", "number", "Feature manifest required"),
        ("Prediction Window", "Unavailable", "number", "Scored production data required"),
    ])
    st.info("Drift indicates a change in data or prediction distributions. It does not automatically mean model failure.")
    feature, prediction = st.tabs(["Feature Drift", "Prediction Drift"])
    with feature:
        section("Feature Distribution Status", "Comparison needs aligned reference and current production windows")
        st.dataframe(pd.DataFrame([
            {"Feature": name, "Metric": "Not selected", "Reference": "Not connected", "Current": "Not connected", "Status": "Unavailable"}
            for name in ["Risk Probability", "Category", "Shipping Mode", "Market", "Product"]
        ]), width="stretch", hide_index=True)
        empty_state("Connect reference and current feature distributions", "Drift statistics require aligned schemas, documented windows and an approved metric. No test statistics have been invented.")
        disabled_panels(["Distribution comparison", "Reference window", "Current window"])
    with prediction:
        section("Prediction Distribution Status", "Production prediction windows are required")
        empty_state("Prediction drift is unavailable", "Connect comparable scored delivery and demand windows before assessing probability or forecast-distribution changes.")
        disabled_panels(["Reference probability distribution", "Current probability distribution", "Distribution distance"])
