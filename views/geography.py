import streamlit as st
from components.charts import bar
from components.section_header import section
from components.kpi_cards import kpis
from components.tables import records_table
from components.empty_states import empty_state
from services.analytics import summary


def render(df):
    verified = bool(df.attrs.get("verified_artifacts", False))
    options = ["Orders", "Delivery Risk", "Demand", "Profitability"]
    if verified and "Sales" in df:
        options.insert(2, "Sales")
    if verified and "Profit" in df:
        options.insert(3, "Recorded Profit")
    metric = st.selectbox("Geographic metric", options)
    if metric == "Profitability":
        empty_state("Profitability geography is unavailable", "No verified profitability dataset or scored model output is connected. Choose Orders, Delivery Risk, or Demand to continue.", "Model Not Connected")
        return
    if metric == "Demand" and "Forecast Demand" not in df:
        empty_state("Demand geography is unavailable", "The connected delivery artifact has no country/region demand key. Product/day forecast records are kept separate and are not joined to orders.", "Data Grain Not Connected")
        return
    actual_metric = {"Delivery Risk": "Risk Probability", "Demand": "Forecast Demand", "Recorded Profit": "Profit"}.get(metric, metric)
    chart_df = df.dropna(subset=["Risk Probability"]) if metric == "Delivery Risk" else df
    if chart_df.empty:
        empty_state("No scores in this geography", "Select a period containing supplied predictions or choose Orders to see all analytical records.")
        return
    if verified:
        st.caption("Order counts, sales, and recorded profit use primary analytical records. Delivery-risk averages use only orders with supplied predictions.")
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True):
        section("Country comparison", "A ranked chart keeps this preview independent of map tiles and geocoding")
        bar(chart_df, "Country", actual_metric, "geo_country", horizontal=True)
        with st.expander("Country-level choropleth · integration preview"):
            st.info("Map geometry is not connected. Verified country identifiers and a supported boundary source are required; no coordinates have been invented.")
    with right, st.container(border=True):
        section("Selected geography", "Inspect the context behind a geographic signal")
        country = st.selectbox("Country detail", sorted(chart_df.Country.dropna().unique()))
        detail = df[df.Country.eq(country)]
        m = summary(detail)
        st.metric("Orders", f'{m["orders"]:,}')
        if verified:
            st.caption(f'Supplied prediction coverage: {detail["Risk Probability"].notna().sum():,} / {len(detail):,}')
        st.metric("Mean delivery risk", f'{m["risk"]:.1%}' if m["risk"] is not None else "N/A")
        st.metric("Forecast demand", f'{m["forecast"]:,.0f}' if m["forecast"] is not None else "Not connected")
    for col, dim in zip(st.columns(2), ["Region", "Market"]):
        with col, st.container(border=True):
            section(f"Ranked {dim.lower()}s", metric)
            bar(chart_df, dim, actual_metric, f"geo_{dim}", horizontal=True)
    section(f"Critical records / {country}", "High and critical delivery signals in the selected geography")
    records_table(detail[detail.Risk.isin(["High", "Critical"])], "geo_records")

