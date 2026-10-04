import plotly.express as px
import streamlit as st
from components.kpi_cards import kpis
from components.section_header import section
from components.charts import show, matrix
from services.analytics import classification, threshold_curve
from services.export_service import csv_bytes
from config import PRODUCTION_THRESHOLD


def render(df):
    st.info("Synthetic outcomes only · changing the analysis threshold never updates production configuration.")
    controls, analysis = st.columns([.8, 2.2], gap="large")
    with controls, st.container(border=True):
        section("Threshold Controls", "Analysis-only evaluation")
        st.html(f'<div class="production-threshold"><span class="eyebrow">PRODUCTION THRESHOLD</span><b>{PRODUCTION_THRESHOLD:.2f}</b><small>Read-only configured value</small></div>')
        value = st.slider("Analysis threshold", 0., 1., PRODUCTION_THRESHOLD, .01, key="analysis_threshold")
        st.caption("This slider affects only synthetic metrics on this page.")
        st.download_button("Download curve", csv_bytes(threshold_curve(df)), "demo-threshold-analysis.csv", "text/csv", width="stretch")
    with analysis:
        m = classification(df, value)
        kpis([
            {"label": "Precision", "value": m["Precision"], "kind": "percent", "caption": "Analysis threshold", "tone": "blue"},
            {"label": "Recall", "value": m["Recall"], "kind": "percent", "caption": "Analysis threshold", "tone": "purple"},
            {"label": "F1", "value": m["F1"], "kind": "percent", "caption": "Analysis threshold", "tone": "green"},
            {"label": "MCC", "value": m["MCC"], "kind": "decimal", "caption": "Analysis threshold", "tone": "amber"},
        ])
        curve = threshold_curve(df)
        with st.container(border=True):
            section("Threshold Performance", "Precision, recall, F1 and MCC across analysis values")
            fig = px.line(curve, x="Threshold", y=["Precision", "Recall", "F1", "MCC"])
            fig.add_vline(x=PRODUCTION_THRESHOLD, line_dash="dash", line_color="#8593ad", annotation_text="Production")
            fig.add_vline(x=value, line_dash="dot", line_color="#8970dc", annotation_text="Analysis")
            show(fig, "threshold_performance", height=330)
    with st.container(border=True):
        section("Confusion Matrix", f"Synthetic outcomes at analysis threshold {value:.2f} · production remains {PRODUCTION_THRESHOLD:.2f}")
        matrix(df, value, "threshold_matrix")
