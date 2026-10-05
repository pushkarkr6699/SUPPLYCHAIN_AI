import streamlit as st
from components.insights import insight_card
from components.kpi_cards import kpis
from services.analytics import alerts


def render(df):
    items = alerts(df)
    caption = "Observed artifact insights" if df.attrs.get("verified_artifacts") else "Observed demo insights"
    kpis([
        ("Critical", sum(i["Severity"] == "Critical" for i in items), "number", caption, "red"),
        ("Attention", sum(i["Severity"] == "Attention" for i in items), "number", caption, "amber"),
        ("Information", sum(i["Severity"] == "Information" for i in items), "number", caption),
    ])
    controls = st.columns([1.2, 1.2, 2])
    category = controls[0].multiselect("Category", ["Risk", "Demand", "Trend", "Anomaly", "Concentration", "Model", "Data"], key="insight_category")
    severity = controls[1].multiselect("Severity", ["Critical", "Attention", "Information"], key="insight_severity")
    search = controls[2].text_input("Search insights", placeholder="Search insight title or description")
    filtered = [item for item in items if (not category or item["Category"] in category) and (not severity or item["Severity"] in severity) and (not search or search.casefold() in (item["Title"] + " " + item["Description"]).casefold())]
    if not filtered:
        st.info("No insights match the selected filters.")
        return
    for index in range(0, len(filtered), 2):
        cols = st.columns(2)
        for col, item in zip(cols, filtered[index:index + 2]):
            with col:
                insight_card(item, df, f"feed_{index}_{item['Category']}", show_evidence=True, show_actions=True)
