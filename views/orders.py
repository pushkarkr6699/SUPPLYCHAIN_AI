from html import escape
import streamlit as st
import plotly.express as px
from components.section_header import section
from components.charts import show
from components.navigation import nav_button, go
from components.kpi_cards import kpis
from components.empty_states import empty_state
from components.status import badge
from services.mock_data import FEATURES
from services.export_service import csv_bytes
from config import DELIVERY_MODEL, PRODUCTION_THRESHOLD


def _signal_card(title, status, body, tone="info"):
    st.html(f'<div class="case-signal"><div class="eyebrow">{escape(title)}</div>{badge(status, tone)}<p>{escape(body)}</p></div>')


def render(df):
    left, main = st.columns([1, 3.3], gap="large")
    with left:
        section("Find a record", "Search the current filter context")
        query = st.text_input("Search order ID", placeholder="Order ID", key="order_search")
        candidates = df[df.Order.str.contains(query, case=False, regex=False)]
        if candidates.empty:
            empty_state("No order found", "Search another ID or broaden the active filters.")
            return
        options = candidates.Order.tolist()
        selected = st.session_state.get("selected_order")
        if selected and selected not in options:
            st.info("The selected order is outside this view. Choose an available record.")
        order = st.selectbox("Order results", options, index=options.index(selected) if selected in options else 0, key="order_result_select")
        st.caption(f"{len(candidates):,} matching demo records")
        st.button("Open delivery view", key="order_delivery_shortcut", on_click=go, args=("delivery",), width="stretch")

    with main:
        st.session_state.selected_order = order
        record = df[df.Order.eq(order)].iloc[0]
        is_predicted_late = record["Risk Probability"] >= PRODUCTION_THRESHOLD
        actual = "Late" if record["Actual Late"] else "On time"
        section(f"Case file · {order}", "Synthetic operational record · safe demo fields only", "ORDER INVESTIGATION")
        st.html(f'<div class="case-status-row">{badge("Predicted " + ("Late" if is_predicted_late else "On time"), "warning" if is_predicted_late else "success")} {badge("Actual " + actual, "neutral")} {badge("Risk: " + str(record.Risk), "danger" if record.Risk == "Critical" else "warning" if record.Risk == "High" else "info")}</div>')
        cards = st.columns(3)
        with cards[0]:
            _signal_card("ORDER PROFILE", "DEMO RECORD", f'{record.Market} · {record.Region} · {record["Shipping Mode"]}')
        with cards[1]:
            _signal_card("DELIVERY SIGNAL", f'{record["Risk Probability"]:.1%} probability', f'{DELIVERY_MODEL} · threshold {PRODUCTION_THRESHOLD:.2f}', "warning" if is_predicted_late else "success")
        with cards[2]:
            _signal_card("PROFITABILITY SIGNAL", "Not connected", "No verified profitability score is available.", "neutral")
        fields = ["Order", "Date", "Market", "Region", "Country", "Category", "Department", "Customer Segment", "Shipping Mode"]
        with st.expander("Order profile", expanded=True):
            st.html('<dl class="record-profile">' + ''.join(f'<div><dt>{escape(field)}</dt><dd>{escape(str(record[field].date()) if field == "Date" else str(record[field]))}</dd></div>' for field in fields) + '</dl>')
        section("Delivery probability", "Prediction versus the configured production threshold")
        st.progress(float(record["Risk Probability"]), text=f'{record["Risk Probability"]:.1%} demo probability · production threshold {PRODUCTION_THRESHOLD:.0%}')
        kpis([
            {"label": "Predicted class", "value": "Late" if is_predicted_late else "On time", "caption": f"{DELIVERY_MODEL} · demo signal", "status": "Above threshold" if is_predicted_late else "Below threshold", "tone": "amber" if is_predicted_late else "green"},
            {"label": "Actual outcome", "value": actual, "caption": "Synthetic outcome label"},
            {"label": "Prediction status", "value": "Consistent" if is_predicted_late == bool(record["Actual Late"]) else "Different", "caption": "Observed demo outcome"},
        ])
        left_chart, details = st.columns([1.7, 1])
        with left_chart, st.container(border=True):
            section("Illustrative feature layout", "Not calculated for this record")
            show(px.bar(FEATURES, x="Contribution", y="Feature", orientation="h", color="Contribution", color_continuous_scale="RdBu"), "order_features")
            st.caption("Record-specific SHAP values are unavailable. Feature contribution does not establish causality.")
        with details, st.container(border=True):
            section("Model details", "Configured metadata · no artifact loaded")
            st.write(f"**Model:** {DELIVERY_MODEL}")
            st.write(f"**Production threshold:** {PRODUCTION_THRESHOLD:.2f}")
            st.write("**Model version:** Not loaded")
            st.write("**Prediction timestamp:** Not available")
        with st.expander("Advanced Record Data"):
            st.dataframe(record.to_frame("Value").astype(str), width="stretch")
        cols = st.columns(4)
        for col, dim in zip(cols[:2], ["Market", "Region"]):
            if col.button(f"Filter by {dim.lower()}", key=f"order_open_{dim}", width="stretch"):
                st.session_state.filters[dim] = [record[dim]]
                st.session_state.pop(f"filter_{dim}", None)
                go("geography")
                st.rerun()
        with cols[2]: nav_button("Explain prediction", "explainability", key="order_explain")
        cols[3].download_button("Download record", csv_bytes(df[df.Order.eq(order)]), f"demo-{order}.csv", "text/csv", width="stretch")
