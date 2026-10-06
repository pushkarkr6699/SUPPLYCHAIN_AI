import streamlit as st
import pandas as pd
import plotly.express as px
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import show
from components.empty_states import empty_state
from components.navigation import nav_button
from services.mock_data import FEATURES, MODEL_COMPARISON, DEMAND_COMPARISON
from services.analytics import summary, threshold_curve
from services.provider import get_service
from config import DELIVERY_MODEL, PRODUCTION_THRESHOLD


def render(df):
    if df.attrs.get("verified_artifacts", False):
        _render_verified(df)
        return
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


def _render_verified(df):
    service = get_service()
    delivery, demand, profitability = st.tabs(["Delivery", "Demand", "Profitability"])
    metadata = service.metadata()
    final, final_name = service.final_summary()
    scored = df.dropna(subset=["Risk Probability", "Actual Late"])
    active_threshold = float(df.attrs.get("production_threshold", PRODUCTION_THRESHOLD))
    with delivery:
        st.info("The analytical dataset and supplied Tuned XGBoost scores are connected. Comparisons describe the January 2018 test set at threshold 0.50; the saved scores use 0.35, selected on the same test predictions.")
        kpis([
            ("Scoring model", df.attrs.get("model_name", metadata.get("Winning model", DELIVERY_MODEL)), "number", "Recorded in supplied score rows"),
            ("Model file", metadata.get("Serialized model", "Not configured"), "number", "Artifact status"),
            ("Threshold", f"{active_threshold:.2f}", "number", "Recorded decision threshold"),
            ("Scored orders", len(scored), "number", f"{len(df):,} analytical orders in current filters"),
        ])
        comparison = service.model_comparison()
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Supplied model comparison", "Test-year metrics at threshold 0.50; different from the saved 0.35 operating point")
            if comparison is None:
                st.info("No model comparison CSV is configured.")
            else:
                metric = "Accuracy" if "Accuracy" in comparison else None
                st.dataframe(comparison, hide_index=True, width="stretch")
                if metric:
                    show(px.bar(comparison, x="Model", y=metric), "verified_models_comparison")
        with right, st.container(border=True):
            section("Feature importance", "Random Forest baseline reference · not the active Tuned XGBoost explanation")
            features = service.feature_importance()
            if features is None:
                st.info("No verified feature-importance CSV is configured.")
            else:
                show(px.bar(features.head(15), x="Importance", y="Feature", orientation="h"), "verified_model_features")
        if final:
            st.caption(f"Summary values are reproduced from {final_name}; they are not recalculated from the scored rows.")
            st.dataframe(pd.DataFrame({"Metric": list(final.keys()), "Supplied value": list(final.values())}), hide_index=True, width="stretch")
        if not scored.empty:
            st.caption(f'Current scored-subset accuracy at recorded threshold {active_threshold:.2f}: {scored["Correct Prediction"].mean():.2%}. Unscored orders are excluded from every prediction metric.')
            section("Threshold performance", "Current supplied test predictions · exploratory threshold analysis")
            show(px.line(threshold_curve(scored), x="Threshold", y=["Precision", "Recall", "F1"]), "verified_models_threshold")
        nav_button("Open Threshold Lab →", "threshold", key="models_to_threshold_verified")
    with demand:
        demand_df = service.records(dataset="demand")
        comparison = service.demand_model_comparison()
        from services.demand_inference import status
        st.info("Demand charts use supplied product/day forecasts. Trained next-day inference is available in Demand Intelligence after parity validation. The defective XGBoost classification row is excluded from regression comparison.")
        st.caption(status()["reason"])
        if comparison is None or comparison.empty:
            empty_state("Regression comparison unavailable", "The source comparison artifact contains no verified regression metrics.")
        else:
            regression_metrics = [c for c in ("MAE", "RMSE", "R2", "WAPE", "SMAPE") if c in comparison and comparison[c].notna().any()]
            section("Demand regression baselines", "Only rows with supplied regression metrics")
            st.dataframe(comparison, hide_index=True, width="stretch")
            if regression_metrics:
                metric = "WAPE" if "WAPE" in regression_metrics else regression_metrics[0]
                chart_df = comparison.dropna(subset=[metric])
                if not chart_df.empty:
                    show(px.bar(chart_df, x="Model", y=metric), "verified_demand_comparison")
        st.caption(f"Connected forecast rows: {len(demand_df):,} web-visit observations. Training precedes January 2018; these outputs are January 2018 test predictions. Source 90% bounds cover approximately 67.63% of supplied rows.")
    with delivery:
        if st.toggle("Inspect final delivery experiment",key="models_final_experiment"):
            from views.final_delivery import render as final_delivery
            final_delivery(key="models_final_delivery")
    with profitability:
        from views.profitability import model_diagnostics
        model_diagnostics(service.records(dataset="profitability"),"model_profitability")

