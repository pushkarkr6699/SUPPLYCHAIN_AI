import streamlit as st
from components.navigation import go
from components.auth_components import login_card


def render():
    with st.container(key="auth_header"):
        brand, back = st.columns([4, 1], vertical_alignment="center")
        with brand:
            st.html('<div class="public-brand"><span class="brand-symbol">S</span><span>SUPPLYCHAIN <b>AI</b><small>Decision Intelligence Platform</small></span></div>')
        with back:
            st.button("Back to site", key="login_header_back", on_click=go, args=("landing",), type="tertiary", width="stretch")

    left, right = st.columns([.96, 1.04], gap="large", vertical_alignment="center")
    with left, st.container(key="auth_brand_panel"):
        st.html('''<section class="auth-brand"><div class="auth-brand-kicker">A CLEARER VIEW OF WHAT'S NEXT</div><h1>Your supply chain intelligence workspace.</h1><p>Explore predictive delivery risk, next-day demand forecasts and operational signals from one unified control tower.</p><div class="auth-brand-rule"></div><div class="auth-feature-list"><div><i>↗</i><span><b>Delivery risk</b><small>Probability, segments and order context</small></span></div><div><i>⌁</i><span><b>Demand forecast</b><small>Product outlook and forecast error</small></span></div><div><i>✧</i><span><b>AI Copilot</b><small>Questions with evidence alongside</small></span></div></div><div class="auth-orbit orbit-one"></div><div class="auth-orbit orbit-two"></div><div class="auth-brand-foot"><span>SUPPLYCHAIN AI</span><i></i><span>DECISION INTELLIGENCE PLATFORM</span></div></section>''')
    with right, st.container(key="auth_form_panel"):
        login_card()

    st.html('<div class="auth-mobile-capabilities"><span>↗ Delivery Risk</span><span>⌁ Demand Forecast</span><span>✧ AI Copilot</span></div><footer class="auth-footer">DEMO AUTHENTICATION · UI PREVIEW · SESSION-ONLY ACCESS</footer>')

