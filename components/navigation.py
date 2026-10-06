import streamlit as st

GROUPS = {
    "COMMAND CENTER": [("overview", "Executive Overview", "space_dashboard")],
    "INTELLIGENCE": [("delivery", "Delivery Intelligence", "local_shipping"), ("demand", "Demand Intelligence", "monitoring"), ("profitability", "Profitability Intelligence", "account_balance_wallet"), ("cross_risk", "Cross-Risk Command Center", "grid_view")],
    "ANALYSIS": [("visualizations", "Visualization Studio", "bar_chart"), ("comparison", "Comparison Studio", "compare_arrows"), ("explorer", "Universal Explorer", "search"), ("orders", "Order Explorer", "inventory_2"), ("geography", "Geographic Intelligence", "public"), ("changes", "What Changed?", "compare_arrows"), ("scenarios", "Scenario Lab", "science")],
    "AI": [("copilot", "SupplyChain Copilot", "auto_awesome"), ("insights", "Insight Center", "lightbulb"), ("alerts", "Alert Center", "notifications")],
    "ML GOVERNANCE": [("models", "Model Intelligence", "hub"), ("explainability", "Explainability", "account_tree"), ("threshold", "Threshold Lab", "tune"), ("drift", "Drift Monitor", "multiline_chart"), ("health", "Model Health", "ecg_heart")],
    "DATA": [("uploads", "Bring Your Data", "upload_file"), ("quality", "Data Quality", "verified"), ("lineage", "Data Lineage", "conversion_path"), ("data", "Data Explorer", "table_view")],
    "OUTPUTS": [("reports", "Reports", "description"), ("downloads", "Downloads", "download")],
    "SYSTEM": [("settings", "Settings", "settings"), ("diagnostics", "Developer / Diagnostics", "code")],
}
ROUTES = {route: (label, group, icon) for group, items in GROUPS.items() for route, label, icon in items}


def go(route, **context):
    if route == "copilot" and st.session_state.get("route") != "copilot":
        st.session_state["copilot_source_page"] = st.session_state.get("route", "overview")
    st.session_state.update(context)
    st.session_state["route"] = route
    st.query_params["page"] = route


def nav_button(label, route, key=None, icon=None, **context):
    st.button(label, key=key or f"go_{route}", icon=f":material/{icon}:" if icon else None,
        on_click=go, args=(route,), kwargs=context, width="stretch")

