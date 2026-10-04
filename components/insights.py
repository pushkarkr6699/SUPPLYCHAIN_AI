from html import escape
import streamlit as st
from components.status import badge
from components.navigation import nav_button, go
from components.evidence import evidence


def apply_insight_filter(item):
    if item.get("Category") == "Risk":
        st.session_state.filters["Risk"] = ["High", "Critical"]
        st.session_state.pop("filter_Risk", None)
    go(item["Route"])


def insight_card(item, df, key, show_evidence=False, show_actions=False):
    tone = {"Critical": "danger", "Attention": "warning"}.get(item["Severity"], "info")
    st.html(f'<div class="insight-card">{badge(item["Severity"], tone)} {badge(item["Category"], "neutral")}<h3>{escape(item["Title"])}</h3><p>{escape(item["Description"])}</p><span class="eyebrow">{item["Records"]:,} DEMO RECORDS</span></div>')
    if show_evidence:
        evidence(df)
    if show_actions:
        cols = st.columns(3)
        with cols[0]: nav_button("Investigate", item["Route"], key=f"insight_{key}")
        with cols[1]: nav_button("Ask Copilot", "copilot", key=f"insight_copilot_{key}")
        cols[2].button("Apply Filter", key=f"insight_filter_{key}", on_click=apply_insight_filter, args=(item,), width="stretch")
    else:
        nav_button("Investigate", item["Route"], key=f"insight_{key}")
