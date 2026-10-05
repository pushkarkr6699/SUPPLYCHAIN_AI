import pandas as pd
import plotly.express as px
import streamlit as st
from html import escape
from components.section_header import section as render_section
from components.kpi_cards import kpis
from components.charts import bar, risk_donut, show, matrix
from components.tables import records_table
from components.navigation import nav_button
from components.status import badge
from services.analytics import summary, aggregate, threshold_curve
from services.mock_data import FEATURES
from services.provider import get_service
from config import PRODUCTION_THRESHOLD, DELIVERY_MODEL


def section(title, subtitle=None, tag=None):
    render_section(title, subtitle, tag, level=2)


def daily_risk_trend(scored):
    """One equally order-weighted mean per calendar day; missing scores stay missing."""
    rows = scored.dropna(subset=["Date", "Risk Probability"]).copy()
    rows["Date"] = pd.to_datetime(rows["Date"]).dt.normalize()
    return rows.groupby("Date", as_index=False, sort=True).agg(
        **{"Risk Probability": ("Risk Probability", "mean"),
           "Scored orders": ("Risk Probability", "count")})


def render(df):
    demo = not df.attrs.get("verified_artifacts", False)
    active_threshold = float(df.attrs.get("production_threshold", PRODUCTION_THRESHOLD))
    model_name = df.attrs.get("model_name", DELIVERY_MODEL)
    scored = df.dropna(subset=["Risk Probability", "Actual Late"])
    source_detail = "Demo fixtures · no model artifact loaded" if demo else f'{len(df):,} orders · {len(scored):,} supplied scores in the current filters'
    st.html(f'<div class="model-meta-row">{badge(model_name, "info")} {badge(f"Threshold {active_threshold:.2f}", "neutral")} {badge("Demo Data" if demo else "Order Data Connected", "success")}<span>{escape(source_detail)}</span></div>')
    m = summary(df)
    score_metrics = summary(scored)
    kpis([
        ("Total Orders", m["orders"], "number", "Demo records" if demo else "Primary order-level dataset"),
        ("High-Risk", m["high"], "number", "High + critical bands" if demo else "High-risk source labels", "red"),
        ("Average Risk", m["risk"], "percent", "Mean probability", "amber"),
        ("Threshold Positive", score_metrics["predicted"], "number", f"Scored orders · threshold ≥ {active_threshold:.2f}"),
        ("Actual Late", m["late"], "number", "Synthetic outcomes" if demo else "Supplied outcome labels", "amber"),
        ("Demo Accuracy" if demo else "Scored Accuracy", score_metrics["accuracy"], "percent", "Synthetic labels only" if demo else "January 2018 scores · test-selected threshold", "purple"),
    ])
    if not demo:
        st.caption(f"Prediction coverage: {len(scored):,} / {len(df):,} orders. Orders without supplied predictions remain unscored; risk charts use scored orders only.")
    overview, segments, diagnostics = st.tabs(["Risk Overview", "Operational Segments", "Model Diagnostics"], key="delivery_active_tab", on_change="rerun")
    if overview.open:
        with overview:
            left, right = st.columns([1.2, 1.8])
            with left, st.container(border=True):
                section("Risk Distribution", "Supplied risk bands" if not demo else "How delivery exposure falls across demo bands")
                if scored.empty:
                    st.info("No supplied scores match the current filters.")
                else:
                    risk_donut(scored, "delivery_distribution")
            with right, st.container(border=True):
                section("Risk Over Time", "Daily mean scored late-delivery probability")
                data = daily_risk_trend(scored)
                fig = px.line(data, x="Date", y="Risk Probability", markers=True, custom_data=["Scored orders"])
                fig.update_traces(hovertemplate="%{x|%d %b %Y}<br>Mean risk: %{y:.1%}<br>Scored orders: %{customdata[0]:,}<extra></extra>")
                fig.update_xaxes(nticks=6)
                fig.update_yaxes(tickformat=".0%")
                show(fig, "delivery_trend")
            section("Critical Orders", "Inspect the strongest delivery signals")
            records_table(df[df.Risk.isin(["High", "Critical"])], "delivery")
    if segments.open:
        with segments:
            dimensions = [d for d in ["Market", "Region", "Shipping Mode", "Category", "Customer Segment"] if d in df][:4]
            for row in [dimensions[i:i + 2] for i in range(0, len(dimensions), 2)]:
                for col, dimension in zip(st.columns(2), row):
                    with col, st.container(border=True):
                        section(f"Risk by {dimension}", "Mean scored late-risk probability")
                        bar(scored, dimension, key=f"delivery_{dimension}", horizontal=True)
            with st.container(border=True):
                section("Risk Heatmap", "Market and shipping combinations · mean scored probability")
                pivot = scored.pivot_table(index="Market", columns="Shipping Mode", values="Risk Probability", aggfunc="mean")
                if not pivot.empty:
                    fig = px.imshow(pivot, text_auto=".0%", color_continuous_scale="Blues", aspect="auto", zmin=0, zmax=1)
                    show(fig, "delivery_heatmap", height=340)
    if diagnostics.open:
        with diagnostics:
            if demo:
                st.info("Diagnostic metrics below are computed from synthetic labels and probabilities. They are illustrative UI values, not verified model performance.")
            else:
                st.info("Diagnostics use supplied January 2018 test scores only. Threshold 0.35 was selected on those test predictions; results do not independently validate that selection. The comparison CSV reports the same model at threshold 0.50.")
            if scored.empty:
                st.info("Choose a date range containing supplied scores to inspect diagnostics.")
            performance, threshold, calibration, explainability = st.tabs(["Performance", "Threshold", "Calibration", "Explainability"])
            with performance:
                left, right = st.columns(2)
                with left, st.container(border=True):
                    section("Confusion Matrix", f'{"Demo outcomes" if demo else "Supplied scored-order outcomes"} · threshold {active_threshold:.2f}')
                    if not scored.empty:
                        matrix(scored, active_threshold, "delivery_matrix")
                with right, st.container(border=True):
                    if demo:
                        section("ROC Curve", "Recall versus false-positive rate on synthetic outcomes")
                        show(px.line(threshold_curve(scored).sort_values("FPR"), x="FPR", y="Recall"), "delivery_roc")
                    else:
                        section("ROC Curve", "Current scored-order subset · descriptive threshold sweep")
                        if not scored.empty:
                            show(px.line(threshold_curve(scored).sort_values("FPR"), x="FPR", y="Recall"), "delivery_roc")
            with threshold:
                with st.container(border=True):
                    section("Precision / Recall Trade-off", "Synthetic evaluation across analysis thresholds" if demo else "Current supplied test scores · exploratory analysis")
                    if not scored.empty:
                        curves = threshold_curve(scored)
                        show(px.line(curves, x="Threshold", y=["Precision", "Recall", "F1"]), "delivery_threshold_curve")
                    else:
                        st.info("Threshold metrics need orders with supplied probabilities and actual outcomes.")
            with calibration:
                bins = pd.cut(scored["Risk Probability"], bins=[0, .2, .4, .6, .8, 1], include_lowest=True)
                data = scored.groupby(bins, observed=True).agg(predicted=("Risk Probability", "mean"), observed=("Actual Late", "mean")).reset_index(drop=True)
                with st.container(border=True):
                    section("Calibration Preview", "Synthetic fixture" if demo else "Supplied test score/outcome relationship · descriptive only")
                    show(px.scatter(data, x="predicted", y="observed", range_x=[0, 1], range_y=[0, 1]), "delivery_calibration")
            with explainability:
                with st.container(border=True):
                    if demo:
                        section("Illustrative Feature Ranking", "Fixture values only · no explanation artifact connected")
                        show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "delivery_features")
                        st.caption("These values do not explain any individual prediction and do not imply causality.")
                    else:
                        section("Feature Importance", "Random Forest baseline reference · a different model from the active scores")
                        features = get_service().feature_importance()
                        if features is not None and not features.empty:
                            show(px.bar(features.head(15), x="Importance", y="Feature", orientation="h"), "delivery_features")
                        st.caption("The supplied ranking describes the earlier Random Forest. It does not explain individual Tuned XGBoost predictions.")
    with st.container(border=True):
        section("Model Context", "Demo configuration" if demo else "Model and threshold recorded in the supplied scores")
        st.write(f"**Model:** {model_name} · **Decision threshold:** {active_threshold:.2f}")
        cols = st.columns(2)
        with cols[0]: nav_button("Explain a prediction", "explainability", key="delivery_explain")
        with cols[1]: nav_button("Explore thresholds", "threshold", key="delivery_threshold")
