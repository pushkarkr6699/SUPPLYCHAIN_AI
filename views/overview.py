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


def render(df):
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
