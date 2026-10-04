import streamlit as st
import plotly.express as px
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import show
from services.analytics import quality
from services.mock_data import DEMO_AS_OF


def render(df):
    dataset = st.selectbox("Dataset", ["Delivery demo records", "Demand demo observations"])
    columns = ["Order", "Date", "Market", "Risk Probability", "Actual Late"] if dataset.startswith("Delivery") else ["Date", "Product", "Market", "Actual Demand", "Forecast Demand", "Lower", "Upper"]
    data = df[columns]
    covered = data["Risk Probability"].notna().mean() if "Risk Probability" in data else data["Forecast Demand"].notna().mean()
    kpis([("Rows", len(data), "number", "Filtered synthetic observations"), ("Columns", len(data.columns), "number", "Selected dataset schema"), ("Missing", data.isna().sum().sum(), "number", "Null cells"), ("Duplicates", data.duplicated().sum(), "number", "Exact row duplicates"), ("Coverage", covered if len(data) else 0, "percent", "Non-null prediction cells"), ("Freshness", "Static fixture", "number", "No live refresh")])
    st.caption(DEMO_AS_OF + " · No opaque quality score is displayed.")
    schema, missing, coverage = st.tabs(["Schema & unique counts", "Missingness & duplicates", "Coverage & validation"])
    with schema:
        st.dataframe(quality(data), hide_index=True, width="stretch")
    with missing:
        section("Missingness by field", "Measured directly from this synthetic view")
        missing_counts = data.isna().sum().rename_axis("Field").reset_index(name="Missing cells")
        left, right = st.columns([1.3, 1])
        with left, st.container(border=True):
            show(px.bar(missing_counts, x="Field", y="Missing cells"), "quality_missingness")
        with right:
            st.dataframe(missing_counts, hide_index=True, width="stretch")
        section("Duplicate rows", "Exact duplicates only; future data needs domain-specific keys")
        dup = data[data.duplicated(keep=False)]
        if dup.empty: st.success("No exact duplicate rows in this demo view.")
        else: st.dataframe(dup, width="stretch")
    with coverage:
        section("Date coverage", "Current workspace filter")
        st.write(f"{df.Date.min():%d %b %Y} – {df.Date.max():%d %b %Y}" if len(df) else "No dates available")
        section("Prediction coverage", "Availability, not accuracy")
        st.write(f"{covered:.1%}" if len(data) else "Unavailable")
        invalid = ((df["Risk Probability"] < 0) | (df["Risk Probability"] > 1)).sum()
        st.write(f"Invalid probabilities outside [0, 1]: {invalid}")
        st.caption("Production schema rules, semantic duplicate keys and freshness SLAs must be provided by the real data service.")

