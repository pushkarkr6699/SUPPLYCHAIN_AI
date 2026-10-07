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
    service = get_service()
    dataset = "demo" if service.demo else "delivery"
    active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == dataset else st.session_state.get("filters_by_dataset", {}).get(dataset, {})
    source = service.records({k: v for k, v in active.items() if k != "Date"}, dataset=dataset)
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
        st.warning("One period has no records. Choose dates within the available dataset history.")
        return
    st.html(f'<div class="compare-banner"><div><span>CURRENT PERIOD</span><b>{current[0]:%d %b %Y} – {current[1]:%d %b %Y}</b></div><i>compared with</i><div><span>{mode.upper()}</span><b>{previous[0]:%d %b %Y} – {previous[1]:%d %b %Y}</b></div></div>')
    changes = change_table(current_df, previous_df)
    kpis([{"label": r.Metric, "value": r["Absolute change"], "kind": "decimal", "caption": "Observed period difference", "delta": r.Direction, "tone": "purple"} for _, r in changes.head(5).iterrows()])
    st.dataframe(changes, hide_index=True, width="stretch", column_config={"Percentage change": st.column_config.NumberColumn(format="percent")})
    st.caption("Percentage-point change applies only to rates. Relative changes are undefined when the comparison value is zero. Overlapping/custom periods may have unequal exposure.")
    if 'Sales' in source and 'Market' in source:
        from services.comparison_service import additive_contributions
        import plotly.graph_objects as go
        section('Sales change contributions','Additive observed sales differences by market, in source monetary units; associations only.')
        try:
            contributions=additive_contributions(current_df,previous_df,'Market','Sales')
            previous_total=float(previous_df.Sales.sum());current_total=float(current_df.Sales.sum())
            labels=['Previous period',*contributions.Market.astype(str),'Current period']
            values=[previous_total,*contributions.Contribution.tolist(),current_total]
            figure=go.Figure(go.Waterfall(x=labels,y=values,measure=['absolute',*['relative']*len(contributions),'total']))
            show(figure,'changes_sales_waterfall',preserve_axis_titles=True)
            st.caption('Contributions sum exactly to current sales minus previous sales. An absent segment contributes zero; unknown observed amounts are never imputed.')
            st.dataframe(contributions,hide_index=True,width='stretch')
        except ValueError as error:st.info(str(error))
    section("Drivers of Observed Change", "Largest contributing segments in the selected periods · associations only")
    dimensions = [name for name in ["Market", "Region", "Category", "Shipping Mode"] if name in source][:3]
    for col, dimension in zip(st.columns(max(1, len(dimensions))), dimensions):
        with col, st.container(border=True):
            section(f"Change by {dimension.lower()}", "Mean delivery-risk difference · percentage points")
            current_agg = aggregate(current_df, dimension).set_index(dimension)
            previous_agg = aggregate(previous_df, dimension).set_index(dimension)
            delta = (current_agg - previous_agg).dropna().reset_index()
            if delta.empty:
                st.info("No comparable supplied scores for this segment in both periods.")
                continue
            delta["Change (pp)"] = delta["Risk Probability"] * 100
            show(px.bar(delta, x=dimension, y="Change (pp)"), f"changes_{dimension}")
    section("Largest observed changes", "Associations and model signals, never causal claims")
    for _, row in changes.iterrows():
        st.write(f'**{row["Metric"]}** · {row["Direction"].lower()} of {abs(row["Absolute change"]):,.3f} in the selected periods.')
    evidence(source[source.Date.isin(pd.concat([current_df.Date, previous_df.Date]))],
        {**{k: v for k, v in active.items() if k != "Date"},
         "Current period": [str(v) for v in current], "Comparison period": [str(v) for v in previous]},
        "Absolute change = current minus comparison; relative change = difference / comparison; rate differences are also expressed in percentage points.")

