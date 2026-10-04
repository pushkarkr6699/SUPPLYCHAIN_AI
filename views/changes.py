from datetime import timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from components.charts import show
from components.section_header import section
from components.kpi_cards import kpis
from components.evidence import evidence
from services.provider import get_service
from services.comparison_service import compare_periods, change_table
from services.analytics import aggregate


def render(df):
    st.caption("Period controls override the global date range on this page. All other workspace filters remain active.")
    source = get_service().records({k: v for k, v in st.session_state.filters.items() if k != "Date"})
    if source.empty:
        st.info("Broaden the workspace filters to compare periods.")
        return
    start, end = source.Date.min().date(), source.Date.max().date()
    a, b, c = st.columns(3)
    current = a.date_input("Current period", value=(max(start, end - timedelta(days=13)), end), min_value=start, max_value=end, key="change_current")
    mode = b.selectbox("Compare with", ["Previous Period", "Previous Equivalent Period", "Custom"])
    if len(current) != 2:
        st.info("Choose a complete current date range.")
        return
    days = (current[1] - current[0]).days + 1
    shift = days if mode != "Previous Equivalent Period" else ((days + 6) // 7) * 7
    previous_default = (current[0] - timedelta(days=shift), current[1] - timedelta(days=shift))
    previous = c.date_input("Comparison period", value=previous_default, key=f"change_compare_{mode}", disabled=mode != "Custom") if mode == "Custom" else previous_default
    if mode != "Custom":
        c.caption(f"{previous[0]:%d %b} – {previous[1]:%d %b %Y}")
    if len(previous) != 2:
        st.info("Choose a complete comparison date range.")
        return
    current_df, previous_df = compare_periods(source, current, previous)
    if current_df.empty or previous_df.empty:
        st.warning("One period has no records. Choose dates within the available demo history.")
        return
    st.html(f'<div class="compare-banner"><div><span>CURRENT PERIOD</span><b>{current[0]:%d %b %Y} – {current[1]:%d %b %Y}</b></div><i>compared with</i><div><span>{mode.upper()}</span><b>{previous[0]:%d %b %Y} – {previous[1]:%d %b %Y}</b></div></div>')
    changes = change_table(current_df, previous_df)
    kpis([{"label": r.Metric, "value": r["Absolute change"], "kind": "decimal", "caption": "Observed period difference", "delta": r.Direction, "tone": "purple"} for _, r in changes.head(5).iterrows()])
    st.dataframe(changes, hide_index=True, width="stretch", column_config={"Percentage change": st.column_config.NumberColumn(format="percent")})
    st.caption("Percentage-point change applies only to rates. Relative changes are undefined when the comparison value is zero. Overlapping/custom periods may have unequal exposure.")
    section("Drivers of Observed Change", "Largest contributing segments in the selected demo periods · associations only")
    for col, dimension in zip(st.columns(3), ["Market", "Region", "Category"]):
        with col, st.container(border=True):
            section(f"Change by {dimension.lower()}", "Mean delivery-risk difference · percentage points")
            current_agg = aggregate(current_df, dimension).set_index(dimension)
            previous_agg = aggregate(previous_df, dimension).set_index(dimension)
            delta = (current_agg - previous_agg).dropna().reset_index()
            delta["Change (pp)"] = delta["Risk Probability"] * 100
            show(px.bar(delta, x=dimension, y="Change (pp)"), f"changes_{dimension}")
    section("Largest observed changes", "Associations and model signals, never causal claims")
    for _, row in changes.iterrows():
        st.write(f'**{row["Metric"]}** · {row["Direction"].lower()} of {abs(row["Absolute change"]):,.3f} in the selected demo periods.')
    evidence(source[source.Date.isin(pd.concat([current_df.Date, previous_df.Date]))],
        {**{k: v for k, v in st.session_state.filters.items() if k != "Date"},
         "Current period": [str(v) for v in current], "Comparison period": [str(v) for v in previous]},
        "Absolute change = current minus comparison; relative change = difference / comparison; rate differences are also expressed in percentage points.")

