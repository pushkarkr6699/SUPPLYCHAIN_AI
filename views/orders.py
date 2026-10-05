from html import escape
import pandas as pd
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
from components.feedback import download_feedback


def _signal_card(title, status, body, tone="info"):
    st.html(f'<div class="case-signal"><div class="eyebrow">{escape(title)}</div>{badge(status, tone)}<p>{escape(body)}</p></div>')


def render(df):
    verified = bool(df.attrs.get("verified_artifacts", False))
    active_threshold = float(df.attrs.get("production_threshold", PRODUCTION_THRESHOLD))
    model_name = df.attrs.get("model_name", DELIVERY_MODEL)
    left, main = st.columns([1, 3.3], gap="large")
    with left:
        section("Find a record", "Search the current filter context")
        query = st.text_input("Search order ID", placeholder="Order ID", key="order_search")
        candidates = df[df.Order.str.contains(query, case=False, regex=False)]
        if candidates.empty:
            empty_state("No order found", "Search another ID or broaden the active filters.")
            return
        options = candidates.Order.drop_duplicates().tolist()
        selected = st.session_state.get("selected_order")
        if selected in options and selected != st.session_state.get("order_last_navigation"):
            st.session_state.order_result_select = selected
            st.session_state.order_last_navigation = selected
        if selected and selected not in options and not query:
            st.caption("The previously selected order is outside this view. Showing an available result below.")
        order = st.selectbox("Order results", options, index=options.index(selected) if selected in options else 0, key="order_result_select")
        st.caption(f'{len(candidates):,} matching {"orders" if verified else "demo records"}')
        st.button("Open delivery view", key="order_delivery_shortcut", on_click=go, args=("delivery",), width="stretch")

    with main:
        st.session_state.selected_order = order
        record = df[df.Order.eq(order)].iloc[0]
        has_score = pd.notna(record.get("Risk Probability"))
        is_predicted_late = (bool(record["Predicted Late"]) if "Predicted Late" in record and pd.notna(record["Predicted Late"]) else record["Risk Probability"] >= active_threshold) if has_score else None
        prediction_label = "Unscored" if not has_score else "Late" if is_predicted_late else "On time"
        actual = "Late" if record["Actual Late"] else "On time"
        risk_label = str(record.Risk) if pd.notna(record.Risk) else "Unscored"
        section(f"Case file · {order}", "Verified order-level analytical record" if verified else "Synthetic operational record · safe demo fields only", "ORDER INVESTIGATION")
        st.html(f'<div class="case-status-row">{badge("Predicted " + prediction_label if has_score else "Unscored", "warning" if is_predicted_late else "success" if has_score else "neutral")} {badge("Actual " + actual, "neutral")} {badge("Risk: " + risk_label, "danger" if risk_label == "Critical" else "warning" if risk_label == "High" else "info")}</div>')
        cards = st.columns(3)
        with cards[0]:
            _signal_card("ORDER PROFILE", "VERIFIED ORDER" if verified else "DEMO RECORD", f'{record.Market} · {record.Region} · {record["Shipping Mode"]}')
        with cards[1]:
            _signal_card("DELIVERY SIGNAL", f'{record["Risk Probability"]:.1%} probability' if has_score else "Unscored", f'{model_name} · threshold {active_threshold:.2f}' if has_score else "No prediction was supplied for this order.", "warning" if is_predicted_late else "success" if has_score else "neutral")
        with cards[2]:
            if "Profit" in record and pd.notna(record["Profit"]):
                _signal_card("RECORDED PROFIT", f'{record["Profit"]:,.2f}', "Recorded order profit; this is not a model prediction.", "neutral")
            else:
                _signal_card("PROFITABILITY SIGNAL", "Not connected", "No verified profitability score is available.", "neutral")
        fields = [field for field in ["Order", "Date", "Market", "Region", "Country", "Category", "Department", "Customer Segment", "Type", "Shipping Mode", "Sales", "Profit"] if field in record]
        with st.expander("Order profile", expanded=True):
            st.html('<dl class="record-profile">' + ''.join(f'<div><dt>{escape(field)}</dt><dd>{escape(str(record[field].date()) if field == "Date" else str(record[field]))}</dd></div>' for field in fields) + '</dl>')
        section("Delivery probability", "Prediction versus the recorded decision threshold")
        if has_score:
            st.progress(float(record["Risk Probability"]), text=f'{record["Risk Probability"]:.1%} {"supplied" if verified else "demo"} probability · decision threshold {active_threshold:.0%}')
        else:
            st.info("The primary dataset contains this order, but the supplied score file does not. No risk estimate or predicted class is inferred from its observed outcome.")
        kpis([
            {"label": "Predicted class", "value": prediction_label, "caption": f"{model_name} · precomputed score" if has_score else "No supplied prediction", "status": "Above threshold" if is_predicted_late else "Below threshold" if has_score else "Unavailable", "tone": "amber" if is_predicted_late else "green" if has_score else "blue"},
            {"label": "Actual outcome", "value": actual, "caption": "Supplied outcome label" if verified else "Synthetic outcome label"},
            {"label": "Prediction status", "value": "Unavailable" if not has_score else "Consistent" if is_predicted_late == bool(record["Actual Late"]) else "Different", "caption": "Supplied prediction agreement" if verified else "Observed demo outcome"},
        ])
        left_chart, details = st.columns([1.7, 1])
        with left_chart, st.container(border=True):
            section("Prediction explanation", "Not available from the scored output")
            if not verified:
                show(px.bar(FEATURES, x="Contribution", y="Feature", orientation="h", color="Contribution", color_continuous_scale="RdBu"), "order_features")
                st.caption("Illustrative layout only. Record-specific SHAP values are unavailable and feature contribution does not establish causality.")
            else:
                st.info("The CSV contains precomputed probabilities and predicted classes, but no feature-level explanation artifact.")
        with details, st.container(border=True):
            section("Model details", "Source metadata for the precomputed score")
            st.write(f"**Model:** {model_name}")
            st.write(f"**Decision threshold:** {active_threshold:.2f}")
            st.write("**Prediction source:** Supplied scored CSV" if verified and has_score else "**Prediction source:** Unavailable" if verified else "**Prediction source:** Demo fixtures")
            st.write("**Prediction timestamp:** Not available")
            st.caption(f"Primary source: {df.attrs.get('artifact', 'Synthetic demo fixture')}")
            st.caption(f"Score source: {df.attrs.get('score_artifact', 'Supplied score file' if verified else 'Demo fixture')}")
        with st.container(border=True, key="order_next_action"):
            section("Next step", "Choose an action supported by this record")
            st.write("Review shipping details and the recorded outcome alongside this estimate. A high score identifies a record for review; it does not explain why the delivery was late." if has_score else "This order has no supplied historical score. Run the registered model explicitly in the Prediction Lab when required source features are available.")
            prediction, report = st.columns(2)
            with prediction: nav_button("Run trained prediction" if verified else "Open demo scenario", "scenarios", key="order_prediction", selected_order=order)
            with report: nav_button("Create delivery brief", "reports", key="order_report", report_type="Delivery")
        with st.expander("Advanced Record Data"):
            st.dataframe(record.to_frame("Value").astype(str), width="stretch")
        cols = st.columns(4)
        for col, dim in zip(cols[:2], ["Market", "Region"]):
            if col.button(f"Filter by {dim.lower()}", key=f"order_open_{dim}", width="stretch"):
                st.session_state.filters[dim] = [record[dim]]
                st.session_state.pop(f'filter_{dim}{"_delivery" if verified else ""}', None)
                go("geography")
                st.rerun()
        with cols[2]: nav_button("Explain prediction", "explainability", key="order_explain")
        cols[3].download_button("Download record", csv_bytes(df[df.Order.eq(order)]), f'{"order" if verified else "demo"}-{order}.csv', "text/csv", width="stretch", on_click=download_feedback, args=("Order download",))
