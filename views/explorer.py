import streamlit as st
import plotly.express as px
from components.section_header import section
from components.navigation import nav_button, ROUTES
from components.kpi_cards import kpis
from components.charts import show
from components.tables import records_table
from services.analytics import summary, alerts
from services.provider import get_service

DIMENSIONS = ["Date", "Market", "Region", "Country", "Category", "Department", "Product", "Shipping Mode", "Customer Segment", "Risk"]
METRICS = ["Orders", "Mean Delivery Risk", "High-Risk Orders", "Forecast Demand", "Actual Demand", "Mean Forecast Error", "Stock Attention"]
METRIC_LABELS = {
    "Orders": "Count of demo records", "Mean Delivery Risk": "Mean synthetic delivery probability",
    "High-Risk Orders": "Count of High and Critical demo bands", "Forecast Demand": "Sum of synthetic forecast units",
    "Actual Demand": "Sum of synthetic demand units", "Mean Forecast Error": "Mean absolute forecast error in units",
    "Stock Attention": "Count under the illustrative attention rule",
}


def grouped_values(df, dimension, metric):
    if metric in {"Profitability Probability", "Loss Probability", "Profit"}:
        return df.groupby(dimension,observed=True)[metric].mean().reset_index(name="Value")
    if metric == "Line items":
        return df.groupby(dimension,observed=True).size().reset_index(name="Value")
    if metric == "Orders":
        return df.groupby(dimension, observed=True).size().reset_index(name="Value")
    if metric == "Mean Delivery Risk":
        return df.groupby(dimension, observed=True)["Risk Probability"].mean().reset_index(name="Value")
    if metric == "High-Risk Orders":
        return df.assign(_value=df.Risk.isin(["High", "Critical"]).astype(int)).groupby(dimension, observed=True)._value.sum().reset_index(name="Value")
    if metric in {"Forecast Demand", "Actual Demand"}:
        return df.groupby(dimension, observed=True)[metric].sum().reset_index(name="Value")
    if metric == "Mean Forecast Error":
        return df.assign(_value=(df["Forecast Demand"] - df["Actual Demand"]).abs()).groupby(dimension, observed=True)._value.mean().reset_index(name="Value")
    return df.assign(_value=df["Stock Attention"].astype(int)).groupby(dimension, observed=True)._value.sum().reset_index(name="Value")


def render(df):
    if df.attrs.get("verified_artifacts"):
        _render_verified(df)
        return
    query = st.text_input("Search the workspace", value=st.session_state.get("search_query", ""), key="explorer_query", placeholder="Pages, metrics, orders, products, countries, markets, reports, insights…")
    st.session_state.search_query = query
    normalized = query.strip().casefold()
    if normalized and normalized not in st.session_state.recent_searches:
        st.session_state.recent_searches = ([query.strip()] + st.session_state.recent_searches)[:6]
    if not normalized:
        section("Suggested Investigations", "Search the workspace or choose a starting point")
        for col, label, route in zip(st.columns(3), ["Review high-risk orders", "Explore product forecasts", "Compare markets"], ["delivery", "demand", "geography"]):
            with col:
                nav_button(label, route, key=f"suggest_{route}")
        if st.session_state.recent_searches:
            st.caption("Recent searches · " + " · ".join(st.session_state.recent_searches))
    else:
        page_hits = [(route, meta) for route, meta in ROUTES.items() if normalized in (route + " " + meta[0] + " " + meta[1]).casefold()]
        if page_hits:
            section("Pages and Capabilities", f"{len(page_hits)} matches")
            for start in range(0, len(page_hits), 3):
                for col, (route, meta) in zip(st.columns(3), page_hits[start:start + 3]):
                    with col:
                        nav_button(meta[0], route, key=f"search_page_{route}")
        metric_hits = [(name, label, route) for name, label, route in [
            ("Delivery Risk", "Mean probability across the current delivery context", "delivery"),
            ("High-Risk Orders", "Records in the High and Critical demo bands", "delivery"),
            ("Forecast Demand", "Synthetic next-day planning units", "demand"),
            ("Forecast Error", "Absolute error in the synthetic forecast preview", "demand"),
            ("Stock Attention", "Illustrative forecast attention rule", "demand"),
            ("Data Quality", "Schema, coverage, nulls, and duplicate checks", "quality"),
        ] if normalized in (name + " " + label).casefold()]
        if metric_hits:
            section("Metrics", "Metric definitions and destinations")
            for start in range(0, len(metric_hits), 3):
                for col, (name, label, route) in zip(st.columns(3), metric_hits[start:start + 3]):
                    with col:
                        st.caption(f"**{name}** · {label}")
                        nav_button("Open analysis", route, key=f"search_metric_{name}")
        alert_hits = [item for item in alerts(df) if normalized in (item["Title"] + " " + item["Description"]).casefold()]
        if alert_hits:
            section("Alerts and Insights", f"{len(alert_hits)} matching demo observations")
            for start in range(0, len(alert_hits), 3):
                for col, item in zip(st.columns(3), alert_hits[start:start + 3]):
                    with col:
                        st.caption(f"**{item['Title']}** · {item['Severity']}")
                        nav_button("Investigate", item["Route"], key=f"search_alert_{item['Category']}")

    section("Build an Exploration", "Dataset → Dimension → Metric → Visualization → Records", "DEMO DATASET")
    cols = st.columns([1.25, 1.5, 1.15])
    dimension = cols[0].selectbox("Dimension", DIMENSIONS, key="selected_dimension")
    metric = cols[1].selectbox("Metric", METRICS, key="selected_metric", help=METRIC_LABELS)
    chart_type = cols[2].selectbox("Visualization", ["Comparison bar", "Trend", "Data table"], key="explorer_chart_type")
    grouped = grouped_values(df, dimension, metric)
    if chart_type != "Data table" and not grouped.empty:
        with st.container(border=True):
            section(f"{metric} by {dimension}", METRIC_LABELS[metric])
            if chart_type == "Trend" or dimension == "Date":
                grouped = grouped.sort_values(dimension)
                show(px.line(grouped, x=dimension, y="Value", markers=True), "explorer_analysis")
            else:
                horizontal = grouped.sort_values("Value", ascending=True) if len(grouped) <= 18 else grouped.nlargest(18, "Value").sort_values("Value")
                show(px.bar(horizontal, x="Value", y=dimension, orientation="h"), "explorer_analysis")
    if not grouped.empty:
        group_options = grouped[dimension].tolist()
        if st.session_state.get("explorer_selected_group") not in group_options:
            st.session_state.pop("explorer_selected_group", None)
        selected_group = st.selectbox("Inspect group records", group_options, key="explorer_selected_group")
        detail = df[df[dimension].eq(selected_group)]
        m = summary(detail)
        kpis([
            ("Records", m["orders"], "number", "Current demo context"),
            ("Mean delivery risk", m["risk"], "percent", "Synthetic signal"),
            ("Forecast units", m["forecast"], "number", "Synthetic demand", "purple"),
        ])
        records_table(detail, "explorer_detail", investigate=True)
    if normalized:
        entity_hits = []
        for field, name in [("Order", "Orders"), ("Product", "Products"), ("Country", "Countries"), ("Market", "Markets"), ("Region", "Regions"), ("Category", "Categories"), ("Department", "Departments")]:
            matches = [value for value in sorted(df[field].unique()) if normalized in str(value).casefold()]
            entity_hits.extend((field, name, value) for value in matches[:8])
        if entity_hits:
            with st.expander(f"Matching records and entities · {len(entity_hits)} matches", expanded=True):
                for field, name, entity in entity_hits:
                    st.caption(f"**{name[:-1]}:** {entity}")
                    if field == "Order":
                        nav_button("Open case file", "orders", key=f"entity_open_{field}_{entity}", selected_order=entity)
                    else:
                        route = "demand" if field == "Product" else "geography"
                        nav_button("Open analysis", route, key=f"entity_open_{field}_{entity}", selected_product=entity if field == "Product" else None)


def _render_verified(df):
    dataset = st.selectbox("Dataset", ["delivery", "demand", "profitability", "delivery_final"], format_func=lambda name: {"delivery":"Delivery orders","demand":"Demand forecasts","profitability":"Profitability line items","delivery_final":"Final delivery line observations"}[name], key="explorer_dataset")
    df = get_service().records(st.session_state.get("filters_by_dataset", {}).get(dataset, {}), dataset=dataset)
    if df.empty:
        st.info("No records match this dataset's filters.")
        return
    dimensions = [name for name in DIMENSIONS if name in df]
    metrics = ["Orders", "Mean Delivery Risk", "High-Risk Orders"] if dataset in {"delivery","delivery_final"} else ["Forecast Demand", "Actual Demand", "Mean Forecast Error", "Stock Attention"]
    if dataset == "delivery_final": metrics = ["Line items","Mean Delivery Risk","High-Risk Orders"]
    if dataset == "profitability": metrics = ["Line items","Profitability Probability","Loss Probability","Profit"]
    left, right = st.columns(2)
    dimension = left.selectbox("Dimension", dimensions, key=f"verified_dimension_{dataset}")
    metric = right.selectbox("Metric", metrics, key=f"verified_metric_{dataset}")
    section(f"{metric} by {dimension}", "Current supplied dataset; missing predictions excluded from risk metrics")
    grouped = grouped_values(df, dimension, metric)
    if not grouped.empty:
        show(px.bar(grouped.nlargest(20, "Value"), x=dimension, y="Value"), "verified_explorer")
        selected = st.selectbox("Inspect group records", grouped[dimension].tolist(), key=f"verified_group_{dataset}_{dimension}")
        records_table(df[df[dimension].eq(selected)], f"explorer_{dataset}", investigate=dataset == "delivery")
