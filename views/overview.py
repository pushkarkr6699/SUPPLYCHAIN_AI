import streamlit as st
from components.section_header import section
from components.kpi_cards import kpis
from components.charts import forecast_chart, risk_donut, bar
from components.tables import records_table
from components.insights import insight_card
from components.model_cards import model_cards
from components.navigation import nav_button
from components.presentation import toggle_presentation
from services.analytics import summary, alerts
from services.provider import get_service


def render(df):
    if df.attrs.get("verified_artifacts"):
        _render_verified(df)
        visualization_entry()
        return
    m = summary(df)
    actions = st.columns([5, 1.3, 1.3, 1.3])
    with actions[1]:
        nav_button("Generate Brief", "reports", key="overview_brief", icon="description")
    with actions[2]:
        st.button("Presentation Mode", key="overview_presentation", icon=":material/fullscreen:", on_click=toggle_presentation, width="stretch")
    with actions[3]:
        nav_button("Ask Copilot", "copilot", key="overview_ask", icon="auto_awesome")

    st.html('<div class="status-strip"><div class="status-item">DATA FRESHNESS<strong>Fixed demo snapshot</strong></div><div class="status-item">DELIVERY MODEL<strong>Demo state</strong></div><div class="status-item">DEMAND MODEL<strong>Demo state</strong></div><div class="status-item">PROFITABILITY<strong>Not connected</strong></div><div class="status-item">SYSTEM<strong>UI operational</strong></div></div>')
    kpis([
        ("Total Orders", m["orders"], "number", "Demo records in view"),
        ("High-Risk Deliveries", m["high"], "number", "High + critical bands", "red"),
        ("Average Risk", m["risk"], "percent", "Mean delivery signal", "amber"),
        ("Forecast Demand", m["forecast"], "number", "Next-day units", "purple"),
        ("Stock Attention", m["stock"], "number", "Illustrative inventory rule", "amber"),
        ("Active Alerts", m["alerts"], "number", "Demo alert categories"),
    ])
    left, right = st.columns([1.65, 1])
    with left, st.container(border=True):
        section("Demand Outlook", "How is demand moving over the selected period?", "DEMO UNITS")
        forecast_chart(df, "overview_forecast")
    with right, st.container(border=True):
        section("Delivery Risk Overview", "Where do orders sit across risk bands?")
        risk_donut(df, "overview_risk")
    left, right = st.columns(2)
    with left, st.container(border=True):
        section("Risk by market", "Mean predicted delivery-risk probability")
        bar(df, "Market", key="overview_market", horizontal=True)
    with right, st.container(border=True):
        section("Demand by category", "Forecast units in the active context")
        bar(df, "Category", "Forecast Demand", key="overview_category")
    with st.container(border=True):
        section("Critical Records", "Start with the strongest delivery signals", "ORDER INTELLIGENCE")
        records_table(df[df.Risk.isin(["Critical", "High"])], "overview")
    section("Executive Insights", "Observed patterns to guide your next investigation")
    items = alerts(df)
    cards = [items[0], items[1], items[-1], items[3]]
    for col, item in zip(st.columns(min(4, len(cards))), cards):
        with col:
            insight_card(item, df, f"overview_{item['Category']}")
    section("System & Model Health", "Transparent status across connected capabilities")
    model_cards()
    visualization_entry()


def visualization_entry():
    with st.container(border=True,key="overview_visualizations"):
        section("Visualization Studio", "Explore all connected sources with 25 chart types, multiple graphs and independent dataset boards.")
        nav_button("Open Visualization Studio", "visualizations", key="overview_visualizations_open", icon="bar_chart")
    with st.container(border=True,key='overview_uploads'):
        section('Bring Your Data', 'Upload your own dataset for 25 visualizations, compatible trained-model predictions and consented Sevika insights.')
        nav_button('Analyze your own dataset', 'uploads', key='overview_uploads_open', icon='upload_file')


def _render_verified(df):
    service = get_service()
    demand_filters = st.session_state.get("filters_by_dataset", {}).get("demand", {})
    demand = service.records(demand_filters, dataset="demand")
    m, forecast = summary(df), summary(demand)
    scored = int(df["Risk Probability"].notna().sum())
    actions = st.columns([5, 1.3, 1.3, 1.3])
    with actions[1]: nav_button("Generate Brief", "reports", key="overview_brief", icon="description")
    with actions[2]: st.button("Presentation Mode", key="overview_presentation", icon=":material/fullscreen:", on_click=toggle_presentation, width="stretch")
    with actions[3]: nav_button("Ask Copilot", "copilot", key="overview_ask", icon="auto_awesome")
    kpis([
        ("Total Orders", len(df), "number", "Primary analytical dataset in view"),
        ("Scored Orders", scored, "number", "Supplied January 2018 predictions"),
        ("High-Risk Deliveries", m["high"], "number", "Among supplied scored orders", "red"),
        ("Average Risk", m["risk"], "percent", "Unscored orders excluded", "amber"),
        ("Forecast Demand", forecast["forecast"], "number", "Separate product/day dataset", "purple"),
        ("Stock Attention", forecast["stock"], "number", "Supplied forecast review flags"),
    ])
    st.caption("Delivery and demand use separate datasets and filter contexts. Demand figures use the current Demand page filters; the datasets are not joined.")
    left, right = st.columns([1.65, 1])
    with left, st.container(border=True):
        section("Demand Outlook", f'{len(demand):,} product/day rows · supplied forecasts and bounds')
        if len(demand): forecast_chart(demand, "overview_forecast")
        else: st.info("No demand records match the Demand page filters.")
    with right, st.container(border=True):
        section("Delivery Risk Overview", "Supplied risk bands; missing scores remain unscored")
        risk_donut(df, "overview_risk")
    left, right = st.columns(2)
    with left, st.container(border=True):
        section("Risk by market", "Mean probability among scored orders")
        bar(df, "Market", key="overview_market", horizontal=True)
    with right, st.container(border=True):
        section("Demand by category", "Forecast next-day web visits in the separate demand context")
        if len(demand): bar(demand, "Category", "Forecast Demand", key="overview_category")
    section("High-Risk Orders", "Supplied Tuned XGBoost predictions")
    records_table(df[df.Risk.eq("High").fillna(False)], "overview")
    section("Executive Insights", "Measured from the connected datasets")
    items = alerts(df)[:2] + alerts(demand)[:1]
    for col, item in zip(st.columns(3), items):
        with col: insight_card(item, df if item["Category"] != "Demand" else demand, f"overview_{item['Category']}")
    section("System & Model Health", "Registered artifacts and current inference availability")
    model_cards()
