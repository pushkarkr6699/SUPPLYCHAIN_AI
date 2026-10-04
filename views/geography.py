import streamlit as st
from components.charts import bar
from components.section_header import section
from components.kpi_cards import kpis
from components.tables import records_table
from components.empty_states import empty_state
from services.analytics import summary


def render(df):
    metric = st.selectbox("Geographic metric", ["Orders", "Delivery Risk", "Demand", "Profitability"])
    if metric == "Profitability":
        empty_state("Profitability geography is unavailable", "No verified profitability dataset or scored model output is connected. Choose Orders, Delivery Risk, or Demand to continue.", "Model Not Connected")
        return
    actual_metric = {"Delivery Risk": "Risk Probability", "Demand": "Forecast Demand"}.get(metric, metric)
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True):
        section("Country comparison", "A ranked chart keeps this preview independent of map tiles and geocoding")
        bar(df, "Country", actual_metric, "geo_country", horizontal=True)
        with st.expander("Country-level choropleth · integration preview"):
            st.info("Map geometry is not connected. Verified country identifiers and a supported boundary source are required; no coordinates have been invented.")
    with right, st.container(border=True):
        section("Selected geography", "Inspect the context behind a geographic signal")
        country = st.selectbox("Country detail", sorted(df.Country.unique()))
        detail = df[df.Country.eq(country)]
        m = summary(detail)
        st.metric("Orders", f'{m["orders"]:,}')
        st.metric("Mean delivery risk", f'{m["risk"]:.1%}')
        st.metric("Demand", f'{m["forecast"]:,}')
    for col, dim in zip(st.columns(2), ["Region", "Market"]):
        with col, st.container(border=True):
            section(f"Ranked {dim.lower()}s", metric)
            bar(df, dim, actual_metric, f"geo_{dim}", horizontal=True)
    section(f"Critical records / {country}", "High and critical delivery signals in the selected geography")
    records_table(detail[detail.Risk.isin(["High", "Critical"])], "geo_records")

