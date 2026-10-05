import streamlit as st
from html import escape
from components.kpi_cards import kpis
from components.status import badge
from components.navigation import nav_button
from services.analytics import alerts
from services.mock_data import DEMO_AS_OF


def render(df):
    items = alerts(df)
    verified = bool(df.attrs.get("verified_artifacts"))
    label = "supplied" if verified else "demo"
    st.session_state.setdefault("alert_statuses", {})
    if verified:
        scope = "delivery" if "Risk Probability" in df else "demand"
        statuses = st.session_state.setdefault("artifact_alert_statuses", {}).setdefault(scope, {})
    else:
        statuses = st.session_state.alert_statuses
    for index in range(len(items)):
        statuses.setdefault(str(index), "New")
    critical = sum(item["Severity"] == "Critical" for item in items)
    attention = sum(item["Severity"] == "Attention" for item in items)
    information = sum(item["Severity"] == "Information" for item in items)
    acknowledged = sum(value == "Acknowledged" for value in statuses.values())
    kpis([
        ("Critical", critical, "number", f"Active {label} alerts", "red"),
        ("Attention", attention, "number", f"Active {label} alerts", "amber"),
        ("Information", information, "number", f"Active {label} alerts"),
        ("Acknowledged", acknowledged, "number", "This session only", "green"),
    ])
    severity = st.multiselect("Severity", ["Critical", "Attention", "Information"], key="alert_severity_filter")
    visible = [(index, item) for index, item in enumerate(items) if not severity or item["Severity"] in severity]
    if not visible:
        st.info("No alerts match the selected severity.")
        return
    selected = st.session_state.get("active_alert_index", visible[0][0])
    if selected not in [index for index, _ in visible]:
        selected = visible[0][0]
    list_col, detail_col = st.columns([1.4, 1], gap="large")
    with list_col:
        for index, item in visible:
            with st.container(border=True):
                tone = {"Critical": "danger", "Attention": "warning"}.get(item["Severity"], "info")
                status = statuses[str(index)]
                st.html(f'<div class="alert-list-row">{badge(item["Severity"], tone)} {badge(status, "success" if status == "Resolved" else "warning" if status == "Acknowledged" else "neutral")} <b>{escape(item["Title"])}</b><small>{item["Records"]:,} {label} records · {escape(str(item["Timestamp"]))}</small></div>')
                st.caption(item["Description"])
                st.caption(f'Source: {item["Source"]} · Timestamp: {item["Timestamp"]} · Evidence: {item["Evidence"]}')
                left, right = st.columns([1, 1])
                if left.button("Selected" if selected == index else "View details", key=f"alert_detail_{index}", width="stretch"):
                    st.session_state.active_alert_index = index
                    st.rerun()
                if status == "New" and right.button("Acknowledge", key=f"alert_ack_{index}", width="stretch"):
                    statuses[str(index)] = "Acknowledged"
                    st.rerun()
                elif status == "Acknowledged" and right.button("Resolve", key=f"alert_resolve_{index}", width="stretch"):
                    statuses[str(index)] = "Resolved"
                    st.rerun()
                elif status == "Resolved" and right.button("Reopen", key=f"alert_reopen_{index}", width="stretch"):
                    statuses[str(index)] = "New"
                    st.rerun()
    item = items[selected]
    with detail_col, st.container(border=True):
        st.html(f'<div class="eyebrow">ALERT DETAIL</div><h2>{item["Title"]}</h2>{badge(item["Severity"], {"Critical":"danger", "Attention":"warning"}.get(item["Severity"], "info"))}')
        st.write(item["Description"])
        st.divider()
        st.write("**Trigger**", item["Description"])
        st.write("**Source / timestamp**", f'{item["Source"]} · {item["Timestamp"]}')
        st.write("**Evidence**", item["Evidence"])
        if item["Category"] == "Risk":
            threshold = float(df.attrs.get("production_threshold", .56))
            st.write("**Metric / threshold**", f"Supplied delivery risk band · classification threshold {threshold:.2f}" if verified else "Delivery risk band · production threshold 0.56 (configured metadata)")
        elif item["Category"] == "Demand":
            st.write("**Metric / threshold**", "Supplied stock-attention flag · inventory availability is not supplied" if verified else "Illustrative stock-attention rule · not an inventory service alert")
        else:
            st.write("**Metric / threshold**", "Informational observation · no production rule configured")
        st.metric(f"Affected {label} records", f"{item['Records']:,}")
        st.caption(f"Context snapshot: {item['Timestamp']} · {label} records · session-only alert workflow")
        nav_button("Investigate", item["Route"], key=f"alert_investigate_{selected}")
