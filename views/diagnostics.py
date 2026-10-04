from importlib.metadata import version, PackageNotFoundError
import platform
import pandas as pd
import streamlit as st
from components.section_header import section
from components.loading_states import skeletons
from components.empty_states import empty_state


def render(df):
    if st.session_state.presentation:
        st.info("Diagnostics are hidden in Presentation Mode. Exit Presentation Mode from the header to inspect runtime details.")
        return
    if not st.session_state.developer_mode:
        empty_state("Developer mode is disabled", "Enable Developer mode in Settings → Privacy / Security to inspect runtime metadata.", "Restricted UI view")
        return
    section("Runtime inventory", "Version information only · no environment variables or secrets")
    runtime = [{"Package": "Python", "Version": platform.python_version()}]
    for package in ["streamlit", "pandas", "plotly", "duckdb", "scikit-learn", "xgboost", "reportlab"]:
        try: installed = version(package)
        except PackageNotFoundError: installed = "Not installed · future backend dependency"
        runtime.append({"Package": package, "Version": installed})
    st.dataframe(pd.DataFrame(runtime), hide_index=True, width="stretch")
    section("Artifact status", "The UI does not scan or open project CSV/PKL files")
    st.dataframe(pd.DataFrame([
        {"Artifact": "Operational data files", "Status": "Not connected"},
        {"Artifact": "Delivery model files", "Status": "Not loaded"},
        {"Artifact": "Demand model files", "Status": "Not loaded"},
        {"Artifact": "Profitability model files", "Status": "Unverified / not connected"},
    ]), hide_index=True, width="stretch")
    section("Performance", "Measured UI timings · not production benchmarks")
    st.write({"Previous page render (ms)": st.session_state.get("last_render_ms", "First render"), "Last mock query (ms)": st.session_state.get("last_query_ms", "Not measured"), "Cache": "In-memory fixture cache", "Cold startup": "Not instrumented"})
    with st.expander("Safe context"):
        st.write({"Current page": st.session_state.route, "Current filters": str(st.session_state.filters), "Selected order": st.session_state.selected_order, "Selected product": st.session_state.selected_product, "Provider version": "demo-ui-v1"})
    with st.expander("Component states · loading, empty, error"):
        skeletons()
        empty_state("No matching records", "Adjust the filter context to populate this state.")
        st.error("Error-state preview: the data service could not be reached. No real failure has been triggered.")

