import streamlit as st
import plotly.express as px
import pandas as pd
from components.section_header import section
from components.charts import show
from components.empty_states import empty_state
from components.kpi_cards import kpis
from services.mock_data import FEATURES
from services.provider import get_service
from config import PRODUCTION_THRESHOLD


def render(df):
    verified = bool(df.attrs.get("verified_artifacts", False))
    message = "The supplied feature ranking belongs to the Random Forest baseline. It does not explain the active Tuned XGBoost scores. Feature importance does not establish causality." if verified else "Feature contribution describes model behavior and does not establish causality. Charts below are illustrative fixtures; real global and record-specific explanations are unavailable."
    st.html(f'<div class="callout">{message}</div>')
    global_tab, local = st.tabs(["Global Explanation", "Record Explanation"])
    with global_tab:
        section("Global feature importance", "Random Forest baseline reference" if verified else "DEMO UI DATA · fixture values")
        if verified:
            features = get_service().feature_importance()
            if features is not None and not features.empty:
                show(px.bar(features.head(20), x="Importance", y="Feature", orientation="h"), "explain_global")
                st.caption("DataCo_Feature_Importance.csv · original Random Forest global ranking; individual Tuned XGBoost contributions are not supplied.")
            else:
                empty_state("Feature importance unavailable", "No verified feature-importance file is configured.")
        else:
            show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "explain_global")
            empty_state("SHAP summary awaits a verified artifact", "Connect validated SHAP outputs with feature names, background data context and model version. No SHAP values have been computed.")
    with local:
        options = df.Order.drop_duplicates().tolist()
        if not options:
            empty_state("No orders in this view", "Broaden the current filters to select an order.")
            return
        previous = st.session_state.get("selected_order")
        order = st.selectbox("Record selector", options, index=options.index(previous) if previous in options else 0)
        st.session_state.selected_order = order
        row = df[df.Order.eq(order)].iloc[0]
        has_score = pd.notna(row.get("Risk Probability"))
        is_late = (bool(row["Predicted Late"]) if "Predicted Late" in row and pd.notna(row["Predicted Late"]) else row["Risk Probability"] >= float(df.attrs.get("production_threshold", PRODUCTION_THRESHOLD))) if has_score else None
        kpis([("Prediction", "Unscored" if not has_score else "Late" if is_late else "On time", "number", "Supplied scored output" if verified and has_score else "No supplied prediction" if verified else "Synthetic prediction"), ("Probability", row["Risk Probability"] if has_score else None, "percent", "Precomputed probability" if verified else "Demo model signal"), ("Explanation", "Unavailable", "number", "No record-specific artifact")])
        section("Individual feature contributions" if verified else "Contribution chart · layout preview", "No per-order explanation artifact was supplied" if verified else "These illustrative features are not explanations for the selected order")
        if not verified:
            show(px.bar(FEATURES, x="Contribution", y="Feature", orientation="h", color="Contribution", color_continuous_scale="RdBu"), "explain_local")
        else:
            st.info("No individual feature contributions are included in the supplied scored output.")

