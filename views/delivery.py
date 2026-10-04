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
from services.provider import get_service
from config import PRODUCTION_THRESHOLD, DELIVERY_MODEL


def render(df):
    demo = not df.attrs.get("verified_artifacts", False)
    source_detail = "Demo fixtures · no model artifact loaded" if demo else f'Scored CSV · {df.attrs.get("artifact_rows", len(df)):,} source rows · exact duplicate rows retained'
    st.html(f'<div class="model-meta-row">{badge(DELIVERY_MODEL, "info")} {badge(f"Threshold {PRODUCTION_THRESHOLD:.2f}", "neutral")} {badge("Demo Data" if demo else "Scored Output Connected", "success")}<span>{source_detail}</span></div>')
    m = summary(df)
    kpis([
        ("Total Orders" if demo else "Scored Rows", m["orders"], "number", "Demo records" if demo else "Line-item rows in supplied scored output"),
        ("High-Risk", m["high"], "number", "High + critical bands" if demo else "High-risk source labels", "red"),
        ("Average Risk", m["risk"], "percent", "Mean probability", "amber"),
        ("Threshold Positive", m["predicted"], "number", f"Threshold ≥ {PRODUCTION_THRESHOLD:.2f}"),
        ("Actual Late", m["late"], "number", "Synthetic outcomes" if demo else "Supplied outcome labels", "amber"),
        ("Demo Accuracy" if demo else "Row Agreement", m["accuracy"], "percent", "Synthetic labels only" if demo else "Supplied prediction/outcome agreement · split provenance unavailable", "purple"),
    ])
    overview, segments, diagnostics = st.tabs(["Risk Overview", "Operational Segments", "Model Diagnostics"])
    with overview:
        left, right = st.columns([1.2, 1.8])
        with left, st.container(border=True):
            section("Risk Distribution", "Supplied risk bands" if not demo else "How delivery exposure falls across demo bands")
            risk_donut(df, "delivery_distribution")
        with right, st.container(border=True):
            section("Risk Over Time", "Mean scored late-delivery probability by date")
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
                    section(f"Risk by {dimension}", "Mean scored late-risk probability")
                    bar(df, dimension, key=f"delivery_{dimension}", horizontal=True)
        with st.container(border=True):
            section("Risk Heatmap", "Market and shipping combinations · mean demo probability")
            pivot = df.pivot_table(index="Market", columns="Shipping Mode", values="Risk Probability", aggfunc="mean")
            if not pivot.empty:
                fig = px.imshow(pivot, text_auto=".0%", color_continuous_scale="Blues", aspect="auto", zmin=0, zmax=1)
                show(fig, "delivery_heatmap", height=340)
    with diagnostics:
        if demo:
            st.info("Diagnostic metrics below are computed from synthetic labels and probabilities. They are illustrative UI values, not verified model performance.")
        else:
            st.info(f'Scored-output diagnostics · {df.attrs.get("artifact", "supplied CSV")}. Evaluation split and training provenance were not supplied; these are row-level descriptions, not an independent validation claim.')
        performance, threshold, calibration, explainability = st.tabs(["Performance", "Threshold", "Calibration", "Explainability"])
        with performance:
            left, right = st.columns(2)
            with left, st.container(border=True):
                section("Confusion Matrix", f'{"Demo outcomes" if demo else "Supplied scored-row outcomes"} · threshold {PRODUCTION_THRESHOLD:.2f}')
                matrix(df, PRODUCTION_THRESHOLD, "delivery_matrix")
            with right, st.container(border=True):
                if demo:
                    section("ROC Curve", "Recall versus false-positive rate on synthetic outcomes")
                    show(px.line(threshold_curve(df).sort_values("FPR"), x="FPR", y="Recall"), "delivery_roc")
                else:
                    section("ROC Curve", "Independent validation split metadata is unavailable")
                    st.info("The scored file does not establish an independent ROC-AUC evaluation set. No AUC is reported.")
        with threshold:
            curves = threshold_curve(df) if demo else get_service().threshold_analysis()
            with st.container(border=True):
                section("Precision / Recall Trade-off", "Synthetic evaluation across analysis thresholds" if demo else "Supplied threshold-analysis artifact · test split provenance not included")
                show(px.line(curves, x="Threshold", y=["Precision", "Recall", "F1"]), "delivery_threshold_curve")
        with calibration:
            bins = pd.cut(df["Risk Probability"], bins=[0, .2, .4, .6, .8, 1], include_lowest=True)
            data = df.groupby(bins, observed=True).agg(predicted=("Risk Probability", "mean"), observed=("Actual Late", "mean")).reset_index(drop=True)
            with st.container(border=True):
                section("Calibration Preview", "Synthetic fixture" if demo else "Supplied score/outcome relationship · no validation split metadata")
                show(px.scatter(data, x="predicted", y="observed", range_x=[0, 1], range_y=[0, 1]), "delivery_calibration")
        with explainability:
            with st.container(border=True):
                if demo:
                    section("Illustrative Feature Ranking", "Fixture values only · no explanation artifact connected")
                    show(px.bar(FEATURES, x="Importance", y="Feature", orientation="h"), "delivery_features")
                    st.caption("These values do not explain any individual prediction and do not imply causality.")
                else:
                    section("Feature Importance", "No verified feature-importance artifact was found")
                    st.info("No feature contributions are inferred from the scored output CSV.")
    with st.container(border=True):
        section("Model Context", "Configured metadata · production artifact not loaded")
        st.write(f"**Configured model:** {DELIVERY_MODEL} · **Production threshold:** {PRODUCTION_THRESHOLD:.2f}")
        cols = st.columns(3)
        with cols[0]: nav_button("Investigate an order", "orders", key="delivery_order")
        with cols[1]: nav_button("Explain a prediction", "explainability", key="delivery_explain")
        with cols[2]: nav_button("Explore thresholds", "threshold", key="delivery_threshold")
