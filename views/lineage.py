import streamlit as st
import json
from pathlib import Path
from config import ROOT
from services.provider import get_service
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
    if not get_service().demo:
        registry_path = ROOT / "metadata" / "data_registry.json"
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            st.error(f"Artifact registry unavailable: {exc}")
            return
        st.info("Artifact lineage records supplied files and their provenance. Training notebooks are archived; pipeline execution is not implied.")
        artifacts = registry.get("artifacts", [])
        for tab, family in zip(st.tabs(["Delivery", "Demand", "Profitability"]), ["delivery", "demand", "profitability"]):
            with tab:
                rows = [item for item in artifacts if item.get("family", "").lower() == family or f"/{family}/" in str(item.get("path", "")).replace("\\", "/")]
                if not rows:
                    empty_state(f"{family.title()} lineage is not connected", "No supplied artifact is recorded for this dataset.", "Not Connected")
                    continue
                flow(["Supplied artifacts", "Schema validation", "Read-only provider", "Dashboard"])
                selector, details = st.columns([1, 1.8], gap="large")
                with selector:
                    selected = st.radio("Registered artifacts", range(len(rows)), format_func=lambda index: Path(rows[index].get("path", rows[index].get("id", "Artifact"))).name, key=f"lineage_artifact_{family}", label_visibility="collapsed")
                artifact = rows[selected]
                with details, st.container(border=True):
                    section(Path(artifact.get("path", "Artifact")).name, artifact.get("role", "Supplied artifact"), "SELECTED ARTIFACT")
                    for label, key in [("Project path", "path"), ("Original source", "source_path"), ("Status", "status"), ("Rows", "rows"), ("SHA-256", "sha256")]:
                        if artifact.get(key) is not None:
                            st.write(f"**{label}:**", str(artifact[key]))
                    columns = artifact.get("columns", artifact.get("required_columns", []))
                    if columns:
                        with st.expander("Recorded schema"):
                            st.write(columns)
                    st.caption("CSV analysis uses supplied values. Model files and notebooks are provenance artifacts unless a validated inference service is explicitly active.")
        return
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
