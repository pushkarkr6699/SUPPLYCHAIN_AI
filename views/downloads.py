import streamlit as st
from datetime import datetime
from components.section_header import section
from services.export_service import csv_bytes, excel_bytes, report_pdf
from services.analytics import threshold_curve
from services.mock_data import MODEL_COMPARISON
from components.charts import forecast_chart
from services.provider import filter_description


def render(df):
    category = st.radio("Download category", ["Filtered Data", "Predictions", "Model Metrics", "Reports", "Charts"], horizontal=True)
    st.caption("All exports include DEMO UI DATA provenance. Record exports use the active workspace filters.")
    with st.container(border=True):
        st.caption("**Current filters** · " + filter_description(st.session_state.filters))
        columns = st.columns(3)
        columns[0].metric("Rows in context", f"{len(df):,}")
        columns[1].metric("Available columns", f"{len(df.columns):,}")
        columns[2].metric("Generated at", datetime.now().astimezone().strftime("%d %b %Y %H:%M %Z"))
    if category == "Filtered Data":
        section("Filtered workspace data", f"{len(df):,} synthetic records")
        a, b = st.columns(2)
        a.download_button("Filtered data · CSV", csv_bytes(df), "demo-filtered-data.csv", "text/csv", width="stretch")
        b.download_button("Filtered data · Excel", excel_bytes(df), "demo-filtered-data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    elif category == "Predictions":
        for col, name, columns in zip(st.columns(2), ["Delivery Scored Orders", "Demand Forecast"], [["Order", "Date", "Market", "Risk Probability", "Risk", "Actual Late"], ["Date", "Product", "Market", "Actual Demand", "Forecast Demand", "Lower", "Upper"]]):
            with col, st.container(border=True):
                section(name, "CSV · synthetic prediction fixture")
                st.download_button("Download CSV", csv_bytes(df[columns]), f"demo-{name.lower().replace(' ', '-')}.csv", "text/csv", key=f"dl_{name}", width="stretch")
    elif category == "Model Metrics":
        a, b = st.columns(2)
        a.download_button("Model Comparison · CSV", csv_bytes(MODEL_COMPARISON), "demo-model-comparison.csv", "text/csv", width="stretch")
        b.download_button("Threshold Analysis · CSV", csv_bytes(threshold_curve(df)), "demo-threshold-analysis.csv", "text/csv", width="stretch")
    elif category == "Reports":
        for col, report in zip(st.columns(3), ["Executive", "Delivery", "Demand"]):
            with col, st.container(border=True):
                section(f"{report} PDF", "KPIs, demand chart, insights and filter context")
                st.download_button("Download PDF", report_pdf(df, report, st.session_state.filters, ["KPIs", "Charts", "Insights"]), f"demo-{report.lower()}.pdf", "application/pdf", key=f"dl_pdf_{report}", width="stretch")
    else:
        section("Chart export · PNG", "Use the camera icon in the chart toolbar to save a PNG. Expand through the chart fullscreen control.")
        forecast_chart(df, "downloads_chart", 350)

