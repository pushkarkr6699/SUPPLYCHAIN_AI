from importlib.metadata import version, PackageNotFoundError
import platform
import pandas as pd
import streamlit as st
from components.section_header import section
from components.loading_states import skeletons
from components.empty_states import empty_state
from services.provider import get_service


def render(df):
    if st.session_state.presentation:
        st.info("Diagnostics are hidden in Presentation Mode. Exit Presentation Mode from the header to inspect runtime details.")
        return
    if not st.session_state.developer_mode:
        empty_state("Developer mode is disabled", "Enable Developer mode in Settings to inspect runtime metadata.", "Restricted UI view")
        return
    section("Runtime inventory", "Version information only · no environment variables or secrets")
    runtime = [{"Package": "Python", "Version": platform.python_version()}]
    for package in ["streamlit", "pandas", "plotly", "duckdb", "scikit-learn", "xgboost", "reportlab"]:
        try: installed = version(package)
        except PackageNotFoundError: installed = "Not installed · future backend dependency"
        runtime.append({"Package": package, "Version": installed})
    st.dataframe(pd.DataFrame(runtime), hide_index=True, width="stretch")
    service = get_service()
    from services.inference_service import status as delivery_status
    from services.demand_inference import status as demand_status
    section("Artifact status", "Fixed registered sources and trained-model validation")
    st.dataframe(pd.DataFrame([
        {"Artifact": "Data files", "Status": "Synthetic fixtures" if service.demo else "Verified historical CSVs"},
        {"Artifact": "Delivery model files", "Status": "Demo only" if service.demo else "Validated; on-demand inference" if delivery_status()["available"] else "Unavailable"},
        {"Artifact": "Demand model files", "Status": "Demo only" if service.demo else "Validated; on-demand inference" if demand_status()["available"] else "Unavailable"},
        {"Artifact": "Profitability model files", "Status": "Demo only" if service.demo else "Registered; conversion fidelity validated; full features required"},
    ]), hide_index=True, width="stretch")
    section("Performance", "Measured UI timings · not production benchmarks")
    st.write({"Previous page render (ms)": st.session_state.get("last_render_ms", "First render"), "Last query (ms)": st.session_state.get("last_query_ms", "Not measured"), "Cache": "In-memory fixture cache" if service.demo else "Source-version CSV and validated join cache", "Cold startup": "Not instrumented"})
    with st.expander("Safe context"):
        st.write({"Current page": st.session_state.route, "Current filters": str(st.session_state.filters), "Selected order": st.session_state.selected_order, "Selected product": st.session_state.selected_product, "Provider": "demo" if service.demo else "verified"})
    with st.expander("Component states · loading, empty, error"):
        skeletons()
        empty_state("No matching records", "Adjust the filter context to populate this state.")
        st.error("Error-state preview: the data service could not be reached. No real failure has been triggered.")

