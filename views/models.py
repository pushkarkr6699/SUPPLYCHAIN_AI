import streamlit as st
import plotly.express as px
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import show
from components.empty_states import empty_state
from components.navigation import nav_button
from services.mock_data import FEATURES, MODEL_COMPARISON, DEMAND_COMPARISON
from services.analytics import summary, threshold_curve
from config import DELIVERY_MODEL, PRODUCTION_THRESHOLD


def render(df):
    delivery, demand, profitability = st.tabs(["Delivery", "Demand", "Profitability"])
    m = summary(df)
    with delivery:
        st.info("Project metadata: XGBoost, production threshold 0.56. Model artifacts and validation metadata are not loaded. All performance displays below are DEMO UI DATA.")
        kpis([("Winning model", DELIVERY_MODEL, "number", "Supplied project metadata"), ("Model version", "Not loaded", "number", "Demo provider: demo-ui-v1"), ("Threshold", f"{PRODUCTION_THRESHOLD:.2f}", "number", "Production configuration"), ("Validation", "Unavailable", "number", "Verified metadata required")])
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Model comparison", "Illustrative comparison fixtures")
            show(px.bar(MODEL_COMPARISON, x="Model", y="Demo accuracy"), "models_comparison")
        with right, st.container(border=True):
            section("Feature importance", "Demo layout, not verified explanation output")
            show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "models_features")
        section("Threshold performance", "Computed from synthetic outcomes")
        show(px.line(threshold_curve(df), x="Threshold", y=["Precision", "Recall", "F1"]), "models_threshold")
        st.caption(f'Demo prediction coverage: {df["Risk Probability"].notna().sum():,} / {len(df):,} records. Production coverage unavailable.')
        nav_button("Open Threshold Lab →", "threshold", key="models_to_threshold")
    with demand:
        kpis([("Active model", "Not loaded", "number", "Forecast UI uses fixtures"), ("WAPE", m["wape"], "percent", "Synthetic forecast evaluation"), ("SMAPE", m["smape"], "percent", "Synthetic forecast evaluation"), ("Coverage", df["Forecast Demand"].notna().mean() if len(df) else 0, "percent", "Demo records with forecasts")])
        section("Baseline comparison", "Illustrative performance fixtures; not validation results")
        show(px.bar(DEMAND_COMPARISON, x="Model", y="Demo WAPE"), "models_demand_baseline")
        empty_state("Demand feature importance is not connected", "A verified importance or explanation artifact is required. The forecast interface is ready for the service response.")
    with profitability:
        empty_state("Profitability model unavailable", "No verified model, comparison metrics or performance metadata are connected.", "Model Not Connected")

