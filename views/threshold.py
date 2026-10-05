import plotly.express as px
import streamlit as st
from components.kpi_cards import kpis
from components.section_header import section
from components.charts import show, matrix
from services.analytics import classification, threshold_curve
from services.export_service import csv_bytes
from config import PRODUCTION_THRESHOLD


def render(df):
    demo = not df.attrs.get("verified_artifacts", False)
    active_threshold = float(df.attrs.get("production_threshold", PRODUCTION_THRESHOLD))
    df = df.dropna(subset=["Risk Probability", "Actual Late"])
    st.info(("Synthetic outcomes only" if demo else "Supplied January 2018 test scores. The recorded threshold was selected on this test set; this is exploratory analysis, not independent threshold validation") + " · changing the analysis threshold never updates the recorded decision threshold.")
    if df.empty:
        st.info("No supplied scores match the current filters. Include January 2018 to analyze the connected predictions.")
        return
    controls, analysis = st.columns([.8, 2.2], gap="large")
    with controls, st.container(border=True):
        section("Threshold Controls", "Analysis-only evaluation")
        st.html(f'<div class="production-threshold"><span class="eyebrow">RECORDED THRESHOLD</span><b>{active_threshold:.2f}</b><small>Read-only source value</small></div>')
        value = st.slider("Analysis threshold", 0., 1., active_threshold, .01, key="analysis_threshold" if demo else "analysis_threshold_verified")
        st.caption(f"This slider affects analysis only and never changes the recorded {active_threshold:.2f} threshold.")
        curve_export = threshold_curve(df)
        st.download_button("Download curve", csv_bytes(curve_export), "demo-threshold-analysis.csv" if demo else "threshold-analysis.csv", "text/csv", width="stretch")
    with analysis:
        m = classification(df, value)
        kpis([
            {"label": "Precision", "value": m["Precision"], "kind": "percent", "caption": "Analysis threshold", "tone": "blue"},
            {"label": "Recall", "value": m["Recall"], "kind": "percent", "caption": "Analysis threshold", "tone": "purple"},
            {"label": "F1", "value": m["F1"], "kind": "percent", "caption": "Analysis threshold", "tone": "green"},
            {"label": "MCC", "value": m["MCC"], "kind": "decimal", "caption": "Analysis threshold", "tone": "amber"},
        ])
        curve = threshold_curve(df)
        curve = curve.rename(columns={"Balanced_Accuracy": "Balanced Accuracy"})
        with st.container(border=True):
            section("Threshold Performance", "Synthetic calculation" if demo else f"Calculated from {len(df):,} supplied test scores in the current filters")
            fig = px.line(curve, x="Threshold", y=["Precision", "Recall", "F1", "MCC"])
            fig.add_vline(x=active_threshold, line_dash="dash", line_color="#8593ad", annotation_text="Recorded")
            fig.add_vline(x=value, line_dash="dot", line_color="#8970dc", annotation_text="Analysis")
            show(fig, "threshold_performance", height=330)
    with st.container(border=True):
        section("Confusion Matrix", f'{"Synthetic outcomes" if demo else "Supplied scored orders"} at analysis threshold {value:.2f} · recorded threshold remains {active_threshold:.2f}')
        matrix(df, value, "threshold_matrix")
