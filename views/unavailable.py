import streamlit as st
from components.navigation import nav_button
from components.status import badge
from components.section_header import section


def show_profitability_requirements():
    st.session_state.show_profitability_requirements = True


def profitability(df):
    st.html('<div class="capability-status"><div class="capability-icon">◷</div><div><div class="eyebrow">CAPABILITY STATUS · MODEL CONNECTION REQUIRED</div><h2>Profitability Intelligence</h2><p>Profitability scoring stays unavailable until a verified model, input contract and prediction output are connected.</p></div><div class="capability-badge">NOT CONNECTED</div></div>')
    st.html('<div class="capability-flow"><span>Data</span><i>→</i><span>Profitability Model</span><i>→</i><span>Probability</span><i>→</i><span>Loss Risk</span><i>→</i><span>Intelligence</span></div>')
    section("Integration readiness", "Each requirement remains unverified in this UI phase.")
    cols = st.columns(4)
    for col, title in zip(cols, ["Dataset", "Model", "Prediction output", "Threshold metadata"]):
        with col:
            st.html(f'<div class="readiness-item"><span class="readiness-indicator"></span><div><b>{title}</b><small>Not connected</small></div></div>')
    st.button("View Data Requirements", icon=":material/arrow_forward:", on_click=show_profitability_requirements)
    if st.session_state.get("show_profitability_requirements"):
        with st.container(border=True):
            section("Integration Requirements", "Required before profitability scoring can be enabled")
            st.markdown("""- Versioned dataset schema and documented target definition
- Verified model artifact with validation and ownership metadata
- Prediction output contract with probability and record identifiers
- Approved decision threshold with source and effective date
- Evidence lineage from input records to returned scores""")
    st.button("Run profitability analysis", disabled=True, help="A verified model and scored data are required")
    nav_button("View System Health", "health", key="profit_health", icon="ecg_heart")


def cross_risk(df):
    cols = st.columns(3)
    for col, title, status, tone in zip(cols, ["Delivery Model Signal", "Profitability Signal", "Combined Risk"], ["Ready · demo interface", "Missing · not connected", "Unavailable"], ["info", "neutral", "neutral"]):
        with col:
            st.html(f'<div class="model-card"><h3>{title}</h3>{badge(status, tone)}</div>')
    st.html('<div class="callout"><b>This view requires verified outputs from both independent predictive models.</b><br>Delivery risk and profitability risk remain separate signals. No combined records or scores are displayed.</div>')
    st.html('<div class="matrix-preview"><div class="risk-matrix"><div><b>Low / Low</b><small>Low delivery · low profit risk</small></div><div><b>High Delivery</b><small>High delivery · low profit risk</small></div><div><b>High Profit Risk</b><small>Low delivery · high profit risk</small></div><div><b>Critical Combined</b><small>High delivery · high profit risk</small></div></div><span class="matrix-disabled">PLANNED VIEW · NO RECORDS POPULATED</span></div>')
    st.button("Combined analysis unavailable", disabled=True, help="Connect both verified model outputs")
    nav_button("Explore delivery signals", "delivery", key="cross_delivery", icon="local_shipping")
