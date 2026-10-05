import streamlit as st
import plotly.express as px
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import show
from services.analytics import quality
from services.mock_data import DEMO_AS_OF
from services.provider import get_service, filter_description


def render(df):
    service = get_service()
    dataset = st.selectbox("Dataset", ["delivery", "demand"], format_func=lambda name: ("Delivery orders" if name == "delivery" else "Demand observations") + (" · demo" if service.demo else " · supplied data"), key="quality_dataset")
    active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == dataset else st.session_state.get("filters_by_dataset", {}).get(dataset, {})
    df = service.records(active, dataset=dataset)
    columns = ["Order", "Date", "Market", "Risk Probability", "Actual Late"] if dataset == "delivery" else ["Date", "Product", "Market", "Actual Demand", "Forecast Demand", "Lower", "Upper"]
    data = df[[column for column in columns if column in df]]
    covered = data["Risk Probability"].notna().mean() if "Risk Probability" in data else data["Forecast Demand"].notna().mean()
    kpis([("Rows", len(data), "number", "Filtered observations"), ("Columns", len(data.columns), "number", "Selected dataset schema"), ("Missing", data.isna().sum().sum(), "number", "Null cells"), ("Duplicates", data.duplicated().sum(), "number", "Exact rows in displayed schema"), ("Coverage", covered if len(data) else 0, "percent", "Non-null prediction cells"), ("Freshness", "Static fixture" if service.demo else "Supplied snapshot", "number", "No live refresh")])
    st.caption((DEMO_AS_OF if service.demo else df.attrs.get("data_source", "Supplied data")) + " · " + filter_description(active, "All records in selected dataset"))
    if dataset == "delivery" and not service.demo:
        st.caption("Orders without supplied scores remain in the analytical dataset. Missing predictions are measured as uncovered orders, never as low risk.")
    schema, missing, coverage = st.tabs(["Schema & unique counts", "Missingness & duplicates", "Coverage & validation"])
    with schema:
        st.dataframe(quality(data), hide_index=True, width="stretch")
    with missing:
        section("Missingness by field", "Measured directly from the selected dataset")
        missing_counts = data.isna().sum().rename_axis("Field").reset_index(name="Missing cells")
        left, right = st.columns([1.3, 1])
        with left, st.container(border=True):
            show(px.bar(missing_counts, x="Field", y="Missing cells"), "quality_missingness")
        with right:
            st.dataframe(missing_counts, hide_index=True, width="stretch")
        section("Duplicate rows", "Exact duplicates within the selected columns")
        dup = data[data.duplicated(keep=False)]
        if dup.empty: st.success("No exact duplicate rows in this view.")
        else: st.dataframe(dup, width="stretch")
    with coverage:
        section("Date coverage", "Current workspace filter")
        st.write(f"{df.Date.min():%d %b %Y} – {df.Date.max():%d %b %Y}" if len(df) else "No dates available")
        section("Prediction coverage", "Availability, not accuracy")
        st.write(f"{covered:.1%}" if len(data) else "Unavailable")
        if "Risk Probability" in data:
            invalid = ((data["Risk Probability"] < 0) | (data["Risk Probability"] > 1)).sum()
            st.write(f"Invalid probabilities outside [0, 1]: {invalid}")
            st.write(f"Orders without a supplied score: {data['Risk Probability'].isna().sum():,}")
        elif {"Lower", "Upper"}.issubset(data):
            st.write(f"Invalid forecast bounds: {(data.Lower > data.Upper).sum():,}")
        st.caption("These checks describe the loaded rows. Snapshot dates do not imply a live source refresh.")

