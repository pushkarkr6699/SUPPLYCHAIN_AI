import streamlit as st
import plotly.express as px
from components.section_header import section
from components.charts import show
from components.empty_states import empty_state
from components.kpi_cards import kpis
from services.mock_data import FEATURES
from config import PRODUCTION_THRESHOLD


def render(df):
    verified = bool(df.attrs.get("verified_artifacts", False))
    st.html('<div class="callout">Feature contribution describes model behavior and does not establish causality. Charts below are illustrative fixtures; real global and record-specific explanations are unavailable.</div>')
    global_tab, local = st.tabs(["Global Explanation", "Record Explanation"])
    with global_tab:
        section("Global feature importance", "DEMO UI DATA · fixture values")
        if verified:
            empty_state("Feature importance unavailable", "The supplied scored CSV contains no feature-importance or SHAP artifact. The serialized model artifact is not connected.")
        else:
            show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "explain_global")
            empty_state("SHAP summary awaits a verified artifact", "Connect validated SHAP outputs with feature names, background data context and model version. No SHAP values have been computed.")
    with local:
        options = df.Order.drop_duplicates().tolist()
        previous = st.session_state.selected_order
        order = st.selectbox("Record selector", options, index=options.index(previous) if previous in options else 0)
        st.session_state.selected_order = order
        row = df[df.Order.eq(order)].iloc[0]
        is_late = bool(row["Predicted Late"]) if "Predicted Late" in row else row["Risk Probability"] >= PRODUCTION_THRESHOLD
        kpis([("Prediction", "Late" if is_late else "On time", "number", "Supplied scored output" if verified else "Synthetic prediction"), ("Probability", row["Risk Probability"], "percent", "Precomputed probability" if verified else "Demo model signal"), ("Explanation", "Unavailable", "number", "No record-specific artifact")])
        section("Contribution chart · layout preview", "These illustrative features are not explanations for the selected order")
        if not verified:
            show(px.bar(FEATURES, x="Contribution", y="Feature", orientation="h", color="Contribution", color_continuous_scale="RdBu"), "explain_local")
        else:
            st.info("No individual feature contributions are included in the supplied scored output.")

