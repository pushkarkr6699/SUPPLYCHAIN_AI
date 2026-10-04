import pandas as pd
import plotly.express as px
import streamlit as st
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import bar, risk_donut, show, matrix
from components.tables import records_table
from components.navigation import nav_button
from components.status import badge
from services.analytics import summary, aggregate, threshold_curve
from services.mock_data import FEATURES
from config import PRODUCTION_THRESHOLD, DELIVERY_MODEL


def render(df):
    st.html(f'<div class="model-meta-row">{badge(DELIVERY_MODEL, "info")} {badge(f"Threshold {PRODUCTION_THRESHOLD:.2f}", "neutral")} {badge("Ready · Demo Data", "success")}<span>Interface ready · model artifact not loaded</span></div>')
    m = summary(df)
    kpis([
        ("Total Orders", m["orders"], "number", "Demo records"),
        ("High-Risk", m["high"], "number", "High + critical bands", "red"),
        ("Average Risk", m["risk"], "percent", "Mean probability", "amber"),
        ("Threshold Positive", m["predicted"], "number", f"Threshold ≥ {PRODUCTION_THRESHOLD:.2f}"),
        ("Actual Late", m["late"], "number", "Synthetic outcomes", "amber"),
        ("Demo Accuracy", m["accuracy"], "percent", "Synthetic labels only", "purple"),
    ])
    overview, segments, diagnostics = st.tabs(["Risk Overview", "Operational Segments", "Model Diagnostics"])
    with overview:
        left, right = st.columns([1.2, 1.8])
        with left, st.container(border=True):
            section("Risk Distribution", "How delivery exposure falls across demo bands")
            risk_donut(df, "delivery_distribution")
        with right, st.container(border=True):
            section("Risk Over Time", "Mean late-risk probability by day")
            data = aggregate(df, "Date")
            fig = px.line(data, x="Date", y="Risk Probability", markers=True)
            fig.update_yaxes(tickformat=".0%")
            show(fig, "delivery_trend")
        section("Critical Orders", "Inspect the strongest delivery signals")
        records_table(df[df.Risk.isin(["High", "Critical"])], "delivery")
    with segments:
        for row in [["Market", "Region"], ["Shipping Mode", "Category"]]:
            for col, dimension in zip(st.columns(2), row):
                with col, st.container(border=True):
                    section(f"Risk by {dimension}", "Mean demo late-risk probability")
                    bar(df, dimension, key=f"delivery_{dimension}", horizontal=True)
        with st.container(border=True):
            section("Risk Heatmap", "Market and shipping combinations · mean demo probability")
            pivot = df.pivot_table(index="Market", columns="Shipping Mode", values="Risk Probability", aggfunc="mean")
            if not pivot.empty:
                fig = px.imshow(pivot, text_auto=".0%", color_continuous_scale="Blues", aspect="auto", zmin=0, zmax=1)
                show(fig, "delivery_heatmap", height=340)
    with diagnostics:
        st.info("Diagnostic metrics below are computed from synthetic labels and probabilities. They are illustrative UI values, not verified model performance.")
        performance, threshold, calibration, explainability = st.tabs(["Performance", "Threshold", "Calibration", "Explainability"])
        with performance:
            left, right = st.columns(2)
            with left, st.container(border=True):
                section("Confusion Matrix", f"Demo outcomes · threshold {PRODUCTION_THRESHOLD:.2f}")
                matrix(df, PRODUCTION_THRESHOLD, "delivery_matrix")
            with right, st.container(border=True):
                section("ROC Curve", "Recall versus false-positive rate on synthetic outcomes")
                show(px.line(threshold_curve(df).sort_values("FPR"), x="FPR", y="Recall"), "delivery_roc")
        with threshold:
            curves = threshold_curve(df)
            with st.container(border=True):
                section("Precision / Recall Trade-off", "Synthetic evaluation across analysis thresholds")
                show(px.line(curves, x="Threshold", y=["Precision", "Recall", "F1"]), "delivery_threshold_curve")
        with calibration:
            bins = pd.cut(df["Risk Probability"], bins=[0, .2, .4, .6, .8, 1], include_lowest=True)
            data = df.groupby(bins, observed=True).agg(predicted=("Risk Probability", "mean"), observed=("Actual Late", "mean")).reset_index(drop=True)
            with st.container(border=True):
                section("Calibration Preview", "Mean demo prediction versus observed synthetic frequency")
                show(px.scatter(data, x="predicted", y="observed", range_x=[0, 1], range_y=[0, 1]), "delivery_calibration")
        with explainability:
            with st.container(border=True):
                section("Illustrative Feature Ranking", "Fixture values only · no explanation artifact connected")
                show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "delivery_features")
                st.caption("These values do not explain any individual prediction and do not imply causality.")
    with st.container(border=True):
        section("Model Context", "Configured metadata · production artifact not loaded")
        st.write(f"**Configured model:** {DELIVERY_MODEL} · **Production threshold:** {PRODUCTION_THRESHOLD:.2f}")
        cols = st.columns(3)
        with cols[0]: nav_button("Investigate an order", "orders", key="delivery_order")
        with cols[1]: nav_button("Explain a prediction", "explainability", key="delivery_explain")
        with cols[2]: nav_button("Explore thresholds", "threshold", key="delivery_threshold")
