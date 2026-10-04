import streamlit as st
from components.landing_components import flow
from components.empty_states import empty_state
from components.section_header import section

PIPELINES = {
    "Delivery": ["DataCo", "Cleaning", "Feature Engineering", "Temporal Split", "XGBoost", "Scored Orders", "Dashboard"],
    "Demand": ["Access Logs", "Product-Day Aggregation", "Complete Grid", "Lag / Rolling Features", "XGBoost", "Forecast Output", "Dashboard"],
}
DESCRIPTIONS = {
    "DataCo": ("Operational order source", "Source manifest not connected"),
    "Cleaning": ("Documented field normalization and data validation", "Transformation code not verified"),
    "Feature Engineering": ("Delivery feature generation", "Feature manifest not connected"),
    "Temporal Split": ("Time-aware training and evaluation split", "Validation manifest not loaded"),
    "XGBoost": ("Configured model family", "Artifact and version not loaded"),
    "Scored Orders": ("Prediction output with record keys and probabilities", "Prediction output contract unavailable"),
    "Dashboard": ("UI consumes service response contracts", "Demo fixture provider active"),
    "Access Logs": ("Product and access observation source", "Source manifest not connected"),
    "Product-Day Aggregation": ("Daily product-level demand aggregation", "Transformation code not verified"),
    "Complete Grid": ("Product and date combinations", "Feature manifest not connected"),
    "Lag / Rolling Features": ("Historical demand windows", "Feature manifest not connected"),
    "Forecast Output": ("Next-day forecast and interval fields", "Forecast output contract unavailable"),
}


def render(df):
    st.info("Target architecture only · these pipelines are not executed or verified in this UI phase.")
    for tab, name in zip(st.tabs(["Delivery", "Demand", "Profitability"]), ["Delivery", "Demand", "Profitability"]):
        with tab:
            if name == "Profitability":
                empty_state("Profitability lineage is not connected", "A verified source, transformation manifest, model artifact and scored output are required.", "Model Not Connected")
                continue
            stages = PIPELINES[name]
            flow(stages)
            selector, details = st.columns([1, 1.8], gap="large")
            with selector:
                stage = st.radio("Pipeline stages", stages, key=f"lineage_stage_{name}", label_visibility="collapsed")
            description, source = DESCRIPTIONS.get(stage, ("Planned pipeline stage", "Metadata unavailable"))
            with details, st.container(border=True):
                section(stage, f"{name} pipeline stage", "SELECTED STAGE")
                st.write("**Artifact:**", "Not verified" if stage != "Dashboard" else "UI service response")
                st.write("**Description:**", description)
                st.write("**Status:**", "Architecture preview · not executed")
                st.write("**Source:**", source)
                st.caption("A production lineage manifest will supply artifact hashes, source identifiers, schema versions and timestamps.")
