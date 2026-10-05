import streamlit as st
import plotly.express as px
from datetime import datetime
from components.section_header import section
from services.export_service import csv_bytes, excel_bytes, report_pdf
from services.analytics import threshold_curve
from services.mock_data import MODEL_COMPARISON
from components.charts import forecast_chart, show
from services.provider import get_service, filter_description


def render(df):
    service = get_service()
    dataset = st.selectbox("Dataset", ["delivery", "demand"], format_func=lambda name: name.title(), key="downloads_dataset")

    def context(name):
        active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == name else st.session_state.get("filters_by_dataset", {}).get(name, {})
        return service.records(active, dataset=name), active

    df, active = context(dataset)
    source = df.attrs.get("data_source", "DEMO UI DATA")
    prefix = "demo" if service.demo else "supplied"
    category = st.radio("Download category", ["Filtered Data", "Predictions", "Model Metrics", "Reports", "Charts"], horizontal=True)
    st.caption(f"Exports preserve source provenance: {source}. Each dataset uses its own filter context.")
    with st.container(border=True):
        st.caption("**Current filters** ? " + filter_description(active, "All records in selected dataset"))
        columns = st.columns(3)
        columns[0].metric("Rows in context", f"{len(df):,}")
        columns[1].metric("Available columns", f"{len(df.columns):,}")
        columns[2].metric("Generated at", datetime.now().astimezone().strftime("%d %b %Y %H:%M %Z"))
    if category == "Filtered Data":
        section("Filtered workspace data", f"{len(df):,} records ? {source}")
        a, b = st.columns(2)
        a.download_button("Filtered data ? CSV", csv_bytes(df), f"{prefix}-{dataset}-filtered-data.csv", "text/csv", width="stretch")
        b.download_button("Filtered data ? Excel", excel_bytes(df), f"{prefix}-{dataset}-filtered-data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    elif category == "Predictions":
        for col, name in zip(st.columns(2), ["delivery", "demand"]):
            with col, st.container(border=True):
                records, _ = context(name)
                wanted = ["Order", "Date", "Market", "Risk Probability", "Risk", "Actual Late", "Predicted Late"] if name == "delivery" else ["Date", "Product", "Category", "Actual Demand", "Forecast Demand", "Lower", "Upper"]
                section("Delivery scored orders" if name == "delivery" else "Demand forecast", records.attrs.get("data_source", "DEMO UI DATA"))
                if name == "delivery":
                    records = records.loc[records["Risk Probability"].notna()]
                    st.caption("Only rows with supplied prediction scores are exported.")
                st.download_button("Download CSV", csv_bytes(records[[column for column in wanted if column in records]]), f"{prefix}-{name}-predictions.csv", "text/csv", key=f"dl_{name}", width="stretch", disabled=records.empty)
    elif category == "Model Metrics":
        if service.demo:
            comparison, curve = MODEL_COMPARISON, threshold_curve(df)
        elif dataset == "delivery":
            comparison, curve = service.model_comparison(), None
            if df["Risk Probability"].notna().any():
                curve = threshold_curve(df.dropna(subset=["Risk Probability", "Actual Late"]))
                curve.attrs.update(df.attrs)
        else:
            comparison, curve = service.demand_model_comparison(), None
        a, b = st.columns(2)
        if comparison is not None and not comparison.empty:
            a.download_button("Model Comparison ? CSV", csv_bytes(comparison, None if service.demo else comparison.attrs.get("data_source", "Supplied model evaluation artifact")), f"{prefix}-{dataset}-model-comparison.csv", "text/csv", width="stretch")
        else:
            a.info("Model comparison is unavailable for this dataset.")
        if curve is not None:
            b.download_button("Threshold Analysis ? CSV", csv_bytes(curve), f"{prefix}-threshold-analysis.csv", "text/csv", width="stretch")
            if not service.demo:
                b.caption("Recomputed on filtered rows with supplied delivery scores; this is not a new held-out evaluation.")
        elif not service.demo and dataset == "demand":
            b.info("Classification thresholds do not apply to demand forecasts.")
    elif category == "Reports":
        for col, report in zip(st.columns(3), ["Executive", "Delivery", "Demand"]):
            with col, st.container(border=True):
                records, report_filters = (df, active) if report == "Executive" else context(report.lower())
                section(f"{report} PDF", records.attrs.get("data_source", "DEMO UI DATA"))
                st.download_button("Download PDF", report_pdf(records, report, report_filters, ["KPIs", "Charts", "Insights"]), f"{prefix}-{report.lower()}.pdf", "application/pdf", key=f"dl_pdf_{report}", width="stretch", disabled=records.empty)
    else:
        section("Chart export ? PNG", "Use the camera icon in the chart toolbar to save a PNG.")
        if dataset == "demand" or service.demo:
            forecast_chart(df, "downloads_chart", 350)
        else:
            data = df.dropna(subset=["Risk Probability"]).groupby("Date", as_index=False)["Risk Probability"].mean()
            if data.empty:
                st.info("No scored rows in the selected delivery context.")
            else:
                show(px.line(data, x="Date", y="Risk Probability"), "downloads_chart", 350)
