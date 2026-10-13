"""Isolated synthetic browser fixture; never registered as business data.

Only scripts/all_chart_types_browser_qa.py launches this on loopback port 8502.
It exercises the same chart builder, style and runtime controls as the app.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import streamlit as st
from components.app_shell import initialize, load_styles
from components.charts import show
from services import visualization_service as viz

st.set_page_config(page_title="Synthetic chart QA only", layout="wide")
initialize()
st.selectbox("Theme", ["Light", "Dark"], key="theme")
load_styles()
with st.container(key="top_header"):
    st.caption("SYNTHETIC TEST FIXTURE - isolated QA; never connected business data")
kind = st.selectbox("Chart type", viz.CHART_TYPES, key="qa_chart_type")
index = np.arange(72)
frame = pd.DataFrame({
    "Date": pd.date_range("2020-01-01", periods=72),
    "Market": np.take(["Test A", "Test B", "Test C"], index % 3),
    "Category": np.take(["Test X", "Test Y"], index % 2),
    "Sales": 20.0 + index * 2,
    "Profit": 5.0 + index * 0.3 + np.sin(index),
    "Units": 1.0 + index % 7,
    "Latitude": 10.0 + index / 10,
    "Longitude": 65.0 + index / 10,
    "Stage": np.take(["Test first", "Test second", "Test third"], index % 3),
    "Stage Order": 1 + index % 3,
})
frame.attrs.update(uploaded=True, data_source="Synthetic isolated QA fixture", dataset="test_only")
result = viz.build(frame, kind, ["Market", "Category"], ["Sales", "Profit", "Units"], "Sum")
st.subheader(kind)
show(result["figure"], "qa_chart", height=600, preserve_axis_titles=True)
st.caption(result["note"])
st.caption("Exact grouped record count: " + str(int(result["table"].Records.sum())))
