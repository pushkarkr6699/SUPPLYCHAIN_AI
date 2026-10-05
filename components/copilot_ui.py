from html import escape
import streamlit as st
import plotly.express as px
from components.navigation import nav_button, go, ROUTES
from components.charts import show
from components.kpi_cards import kpis
from services.export_service import csv_bytes
from services.provider import filter_description, get_service


def context_drawer(df=None, filters=None):
    service = get_service()
    if df is None:
        dataset = "demo" if service.demo else st.session_state.get("active_filter_dataset", "delivery")
        if dataset not in {"delivery", "demand"} and not service.demo:
            dataset = "delivery"
        df = service.records(st.session_state.get("filters", {}), dataset=dataset)
    active = st.session_state.get("filters", {}) if filters is None else filters
    current = st.session_state.get("copilot_source_page", st.session_state.route)
    st.html('<div class="copilot-context"><span class="eyebrow">WORKSPACE CONTEXT</span><h3>Connected to your view.</h3><p>The offline preview uses the same filters and selected entities.</p></div>')
    st.write("**Current page**", ROUTES.get(current, (current,))[0])
    st.write("**Filters**", filter_description({k: v for k, v in active.items() if k != "Date"}, "All records in selected dataset"))
    st.write("**Selected order**", st.session_state.selected_order or "None")
    st.write("**Selected product**", st.session_state.selected_product or "None")
    st.write("**Date range**", filter_description({"Date": active.get("Date", [])}, "Full dataset date range"))
    st.caption("Dataset: " + df.attrs.get("data_source", "DEMO UI DATA") + "\n\nAnalysis uses available rows; no external AI model is called.")


def response_card(response, provenance, key):
    st.markdown(f'**{response["title"]}**')
    st.write(response["narrative"])
    if response["intent"] != "unsupported":
        m = response["summary"]
        verified = response.get("evidence_context", {}).get("verified_artifacts", False)
        cards = [("Records analyzed", response["records"], "number", "Supplied snapshot" if verified else "Synthetic snapshot")]
        if m.get("risk") is not None:
            cards.append(("Mean delivery risk", m["risk"], "percent", "Scored rows only" if verified else "Demo probability"))
        if m.get("forecast") is not None:
            cards.append(("Forecast demand", m["forecast"], "number", "Next-day visits" if verified else "Demo units", "purple"))
        kpis(cards)
        if not response["chart"].empty:
            show(px.bar(response["chart"], x=response["chart_x"], y=response["chart_y"]), f"copilot_chart_{key}", 220)
        st.dataframe(response["table"], hide_index=True, width="stretch")
    with st.expander("Evidence · dataset, filters, calculation and model"):
        for name, value in provenance.items():
            st.write(f"**{name}**", value)
        st.caption("This answer preserves the filter snapshot at the time of the question.")
    cols = st.columns(4)
    with cols[0]: nav_button("View in dashboard", response["route"], key=f"copilot_view_{key}")
    if cols[1].button("Apply high-risk filter", key=f"copilot_apply_{key}", disabled=response["intent"] != "risk", width="stretch"):
        st.session_state.filters["Risk"] = ["High", "Critical"]
        dataset = "demo" if get_service().demo else "delivery"
        st.session_state.setdefault("filters_by_dataset", {})[dataset] = dict(st.session_state.filters)
        st.session_state.active_filter_dataset = dataset
        st.session_state.pop("filter_Risk", None)
        st.session_state.pop("filter_Risk_delivery", None)
        go("delivery")
        st.rerun()
    orders = response["table"].get("Order")
    if orders is not None and len(orders):
        with cols[2]: nav_button("Open record", "orders", key=f"copilot_record_{key}", selected_order=orders.iloc[0])
    prefix = "supplied" if response.get("evidence_context", {}).get("verified_artifacts") else "demo"
    cols[3].download_button("Download result", csv_bytes(response["table"]), f"{prefix}-copilot-result.csv", "text/csv", key=f"copilot_download_{key}", disabled=response["table"].empty, width="stretch")

