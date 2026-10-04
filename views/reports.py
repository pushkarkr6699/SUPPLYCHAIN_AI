import streamlit as st
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import forecast_chart
from components.empty_states import empty_state
from components.tables import records_table
from services.analytics import summary
from services.export_service import report_pdf
from services.provider import filter_description


def render(df):
    cols = st.columns(5)
    for col, name in zip(cols, ["Executive", "Delivery", "Demand", "Profitability", "Cross-Risk"]):
        with col:
            ready = name in ["Executive", "Delivery", "Demand"]
            st.html(f'<div class="model-card"><h3>{name} Report</h3><span class="badge badge-{ "info" if ready else "neutral" }">{ "Demo report available" if ready else "Model not connected" }</span><p>PDF · current filter context</p></div>')
    left, right = st.columns([1, 2.5], gap="large")
    with left, st.container(border=True):
        section("Report configuration", "Date and filters are inherited from the workspace")
        report = st.selectbox("Report type", ["Executive", "Delivery", "Demand", "Profitability", "Cross-Risk"])
        st.caption(filter_description(st.session_state.filters))
        sections = st.multiselect("Sections", ["KPIs", "Charts", "Insights", "Records"], default=["KPIs", "Charts", "Insights"])
        available = report in ["Executive", "Delivery", "Demand"] and bool(sections) and len(df) > 0
        if st.button("Preview report", width="stretch", disabled=not available):
            st.session_state.report_preview = True
        signature = (report, tuple(sections), str(st.session_state.filters), tuple(df.Order))
        generate_label = "Generate Executive Report" if report == "Executive" else "Generate PDF"
        if st.button(generate_label, type="primary", width="stretch", disabled=not available):
            with st.spinner("Preparing your demo report…"):
                st.session_state.generated_report = (signature, report_pdf(df, report, st.session_state.filters, sections))
            st.success("Demo PDF generated. Ready to download.")
        generated = st.session_state.get("generated_report")
        if generated and generated[0] == signature:
            st.download_button("Download PDF", generated[1], f"demo-{report.lower()}-report.pdf", "application/pdf", width="stretch")
        elif generated:
            st.caption("Report settings changed. Generate again to download an up-to-date PDF.")
    with right:
        if report in ["Profitability", "Cross-Risk"]:
            empty_state(f"{report} report unavailable", "Verified profitability signals must be connected before this report can be generated.", "Model Not Connected")
        elif not sections:
            st.info("Choose one or more report sections.")
        elif st.session_state.get("report_preview"):
            section(f"{report} report / preview", "DEMO UI DATA · exports include the selected sections and filter context")
            m = summary(df)
            if "KPIs" in sections:
                kpis([("Orders", m["orders"], "number", "Demo view"), ("Risk", m["risk"], "percent", "Demo view"), ("Forecast", m["forecast"], "number", "Demo view")])
            if "Charts" in sections:
                forecast_chart(df, "report_preview_forecast")
            if "Insights" in sections:
                st.write(f'{m["high"]:,} demo orders are in high/critical risk bands. {m["stock"]:,} demo observations exceed the illustrative stock-attention rule.')
            if "Records" in sections:
                records_table(df.nlargest(10, "Risk Probability"), "report_preview")
        else:
            empty_state("Build a focused decision brief", "Select sections, preview the current context, then generate a downloadable demo PDF.", "REPORT WORKSPACE")

