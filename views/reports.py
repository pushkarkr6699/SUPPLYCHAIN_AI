import pandas as pd
import plotly.express as px
import streamlit as st
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import forecast_chart, show
from components.empty_states import empty_state
from components.tables import records_table
from services.analytics import summary
from services.export_service import report_pdf
from services.provider import get_service, filter_description
from components.feedback import download_feedback


def render(df):
    service = get_service()
    prefix = "demo" if service.demo else "supplied"
    cols = st.columns(5)
    for col, name in zip(cols, ["Executive", "Delivery", "Demand", "Profitability", "Cross-Risk"]):
        with col:
            ready = name in ["Executive", "Delivery", "Demand"] or not service.demo
            status = ("Demo report available" if service.demo else "Artifact report available") if ready else "Model not connected"
            st.html(f'<div class="model-card"><h3>{name} Report</h3><span class="badge badge-{ "info" if ready else "neutral" }">{status}</span><p>PDF · current filter context</p></div>')
    left, right = st.columns([1, 2.5], gap="large")
    with left, st.container(border=True):
        section("Report configuration", "Each dataset uses its own workspace filters")
        report = st.selectbox("Report type", ["Executive", "Delivery", "Demand", "Profitability", "Cross-Risk"], key="report_type")
        dataset = "demand" if report == "Demand" else "profitability" if report == "Profitability" and not service.demo else "delivery"
        if report == "Executive" and not service.demo:
            dataset = st.selectbox("Executive report scope", ["delivery", "demand"], format_func=str.title, key="reports_scope")
        active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == dataset else st.session_state.get("filters_by_dataset", {}).get(dataset, {})
        df = service.records(active, dataset=dataset)
        if report == "Cross-Risk" and not service.demo:
            from services.profitability_data import cross_risk
            df=cross_risk(df)
        source = df.attrs.get("data_source", "DEMO UI DATA")
        st.caption(filter_description(active, "All records in selected dataset"))
        st.caption(source)
        sections = st.multiselect("Sections", ["KPIs", "Charts", "Insights", "Records"], default=["KPIs", "Charts", "Insights"])
        available = (report in ["Executive", "Delivery", "Demand"] or not service.demo) and bool(sections) and len(df) > 0
        if st.button("Preview report", width="stretch", disabled=not available):
            st.session_state.report_preview = True
        signature = (report, dataset, tuple(sections), str(active), source, int(pd.util.hash_pandas_object(df, index=True).sum()))
        generate_label = "Generate Executive Report" if report == "Executive" else "Generate PDF"
        generated = st.session_state.get("generated_report")
        current = bool(generated and generated[0] == signature)
        if st.button(generate_label, type="primary", width="stretch", disabled=not available or current, key="generate_report_pdf"):
            try:
                with st.spinner("Preparing your report…", show_time=True):
                    st.session_state.generated_report = (signature, report_pdf(df, report, active, sections))
                st.success("PDF generated. Ready to download.")
                st.rerun()
            except (ValueError, RuntimeError, OSError):
                st.error("The report could not be generated. Your configuration is preserved; retry Generate PDF.")
        generated = st.session_state.get("generated_report")
        if generated and generated[0] == signature:
            st.success("Your current report is ready. Change its configuration to generate a new version.")
            st.download_button("Download PDF", generated[1], f"{prefix}-{report.lower()}-report.pdf", "application/pdf", width="stretch", on_click=download_feedback, args=("PDF download",))
        elif generated:
            st.caption("Report settings changed. Generate again to download an up-to-date PDF.")
    with right:
        if report in ["Profitability", "Cross-Risk"] and service.demo:
            empty_state(f"{report} report unavailable", "Verified profitability signals must be connected before this report can be generated.", "Model Not Connected")
        elif not sections:
            st.info("Choose one or more report sections.")
        elif df.empty:
            st.info("No records match this dataset's filters.")
        elif st.session_state.get("report_preview"):
            section(f"{report} report / preview", f"{source} · selected sections and dataset filter context")
            if report in {"Profitability","Cross-Risk"}:
                st.dataframe(df.head(100),hide_index=True,width="stretch")
                st.caption(df.attrs.get("evaluation_note","Historical source evidence"))
                st.caption("PDF includes selected KPIs, chart, insights, records and provenance. This preview shows up to 100 supporting rows.")
                return
            m = summary(df)
            demand = "Forecast Demand" in df and (dataset == "demand" or service.demo)
            if "KPIs" in sections:
                if demand:
                    kpis([("Observations", len(df), "number", "Selected dataset"), ("Forecast", m["forecast"], "number", "Next-day visits"), ("WAPE", m["wape"], "percent", "Supplied forecasts")])
                else:
                    kpis([("Orders", len(df), "number", "Selected dataset"), ("Scored orders", df["Risk Probability"].notna().sum(), "number", "Supplied probabilities"), ("Mean risk", m["risk"], "percent", "Scored rows only")])
            if "Charts" in sections:
                if demand:
                    forecast_chart(df, "report_preview_forecast")
                else:
                    chart = df.dropna(subset=["Risk Probability"]).copy()
                    chart["Date"] = pd.to_datetime(chart["Date"]).dt.normalize()
                    chart = chart.groupby("Date", as_index=False)["Risk Probability"].mean()
                    if chart.empty:
                        st.info("No supplied scores in this report context.")
                    else:
                        figure = px.line(chart, x="Date", y="Risk Probability", markers=True)
                        figure.update_yaxes(tickformat=".0%")
                        figure.update_traces(hovertemplate="%{x|%d %b %Y}<br>Daily mean risk: %{y:.1%}<extra></extra>")
                        show(figure, "report_preview_risk")
            if "Insights" in sections:
                if demand:
                    st.write("Forecast errors compare supplied next-day actual visits and predictions. Interval calibration is not assumed.")
                else:
                    st.write(f'{df["Risk Probability"].notna().sum():,} of {len(df):,} orders have supplied scores. Missing probabilities are excluded from risk averages.')
            if "Records" in sections:
                records = df.head(10) if dataset == "demand" else df.sort_values("Risk Probability", ascending=False, na_position="last").head(10)
                records_table(records, f"report_preview_{dataset}", investigate=dataset == "delivery")
        else:
            empty_state("Build a focused decision brief", "Select sections, preview the current context, then generate a downloadable PDF.", "REPORT WORKSPACE")
