from html import escape
import streamlit as st
from components.status import badge
from components.evidence import evidence
from components.navigation import nav_button
from services.mock_data import DEMO_AS_OF


def remember_review(key):
    st.session_state.reviewed_alerts[key] = st.session_state[f"alert_reviewed_{key}"]


def alert_card(item, df, key):
    with st.container(border=True):
        left, right = st.columns([5, 1])
        with left:
            st.html(f'{badge(item["Severity"], {"Critical":"danger", "Attention":"warning"}.get(item["Severity"], "info"))}<h3>{escape(item["Title"])}</h3>')
            st.write(item["Description"])
            st.caption(f'{DEMO_AS_OF} · {item["Records"]:,} affected demo records')
            evidence(df)
        with right:
            nav_button("Investigate", item["Route"], key=f"alert_{key}")
            st.checkbox("Reviewed", key=f"alert_reviewed_{key}", value=st.session_state.reviewed_alerts.get(key, False),
                on_change=remember_review, args=(key,), help="Saved for this demo session only")

