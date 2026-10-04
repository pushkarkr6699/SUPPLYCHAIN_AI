import streamlit as st
from html import escape
from components.status import badge
from components.navigation import nav_button
from components.section_header import section
from services.health_service import checks


def render(df):
    data = checks(df)
    disconnected = int(data.Status.isin(["Not Connected", "Partial"]).sum())
    tone = "warning" if disconnected else "success"
    st.html(f'<div class="health-banner"><div><span class="eyebrow">OVERALL UI HEALTH</span><h2>{"Integration readiness needed" if disconnected else "Operational"}</h2><p>Application is available. Demo services are isolated, and live model and data connections remain explicit.</p></div>{badge(f"{disconnected} integration checks", tone)}</div>')
    section("Component Health", "Select a component to inspect its service readiness.")
    for start in range(0, len(data), 4):
        cols = st.columns(4)
        for col, (_, row) in zip(cols, data.iloc[start:start + 4].iterrows()):
            with col, st.container(border=True):
                status = row.Status
                badge_tone = {"Operational": "success", "Demo UI": "info", "Session-only": "info", "Not Connected": "warning", "Partial": "warning"}.get(status, "neutral")
                st.html(f'<div class="eyebrow">COMPONENT</div><h3>{escape(row.Component)}</h3>{badge(status, badge_tone)}<p class="health-details">{escape(row.Details)}</p>')
                nav_button("Open diagnostics", row.Action, key=f"health_component_{row.Component}")
    with st.expander("Check details", icon=":material/monitor_heart:"):
        st.dataframe(data, hide_index=True, width="stretch")
        st.caption(f"Last checked: {data['Last Check'].iloc[0] if len(data) else 'Unavailable'}")
    if st.button("Refresh checks", icon=":material/refresh:"):
        st.rerun()
