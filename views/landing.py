from components.brand import MARK
import streamlit as st
from components.landing_components import CAPABILITIES, capability_card, landing_heading, dashboard_preview, hero_preview, flow
from components.navigation import go
from services.auth_service import enter_demo
from services.mock_data import LANDING_DEMO


def render():
    with st.container(key="public_header"):
        brand, links, signin, launch = st.columns([1.48, 3.55, .85, 1.38], vertical_alignment="center")
        with brand:
            st.html('<a class="public-brand" href="#top" aria-label="SupplyChain AI home"><span class="brand-symbol">' + MARK + '</span><span>SUPPLYCHAIN <b>AI</b><small>Decision Intelligence Platform</small></span></a>')
        with links:
            st.html('<nav class="public-links" aria-label="Main navigation"><a href="#platform">Platform</a><a href="#intelligence">Intelligence</a><a href="#copilot">AI Copilot</a><a href="#governance">Governance</a><a href="#architecture">Architecture</a></nav>')
        with signin:
            st.button("Sign in", key="landing_signin", on_click=go, args=("login",), width="stretch")
        with launch:
            st.button("Open platform", key="landing_open_platform", type="primary", on_click=enter_demo, icon=":material/arrow_outward:", width="stretch")

    st.html('<div id="top"></div>')
    hero, preview = st.columns([1.02, .98], gap="large", vertical_alignment="center")
    with hero:
        st.html('<div class="hero"><div class="hero-kicker"><span class="hero-kicker-mark">✳</span> AI-powered supply chain decision intelligence</div><h1>Predict risk.<br>Forecast demand.<br><span>Act with intelligence.</span></h1><p class="hero-copy">Bring delivery-risk signals, next-day demand forecasts and operational investigations into one traceable decision-intelligence workspace.</p><p class="hero-supporting">Turn verified model outputs into clearer operational context and confident next steps.</p></div>')
        primary, secondary = st.columns([1.06, 1], gap="small")
        primary.button("Explore the workspace", key="hero_open_platform", type="secondary", icon=":material/arrow_outward:", on_click=enter_demo, width="stretch")
        secondary.link_button("Explore capabilities", "#platform", width="stretch")
        st.html('<div class="hero-proof"><span>Delivery intelligence</span><i></i><span>Demand forecasting</span><i></i><span>Inspectable ML</span><i></i><span>AI Copilot</span></div>')
    with preview:
        hero_preview()
    st.html('<div class="demo-disclaimer"><span class="demo-dot" aria-hidden="true"></span> Read-only examples · Synthetic values · Open the platform to use the connected workspace</div>')

    st.html('<div class="capability-strip" aria-label="Platform capabilities"><span class="strip-label">ONE WORKSPACE</span><span><i>↗</i> Delivery prediction</span><span><i>⌁</i> Demand forecasting</span><span><i>≋</i> Explainability</span><span><i>⌘</i> Scenario analysis</span><span><i>◈</i> ML governance</span><span><i>✧</i> AI Copilot</span></div>')

    landing_heading("platform", "Why SupplyChain AI", "One platform for prediction, investigation and decision support.", "Designed to help operational teams move from a signal to a focused investigation, while keeping model and data context in view.")
    problem_cards = [
        ("01", "Delivery risk intelligence", "See which delivery records may need attention, then investigate the segments and thresholds behind the signal.", ["Risk probabilities", "Risk bands and markets", "Critical-order review", "Threshold and explanation views"]),
        ("02", "Demand intelligence", "Review next-day product forecasts alongside historical demand, forecast error and illustrative uncertainty ranges.", ["Actual vs forecast", "Demand bands", "Forecast error and trends", "Stock-attention indicators"]),
        ("03", "AI-assisted investigation", "Move from dashboard context to a conversational analytical preview, with evidence attached to the question.", ["Ask focused questions", "Compare segments", "Apply workspace filters", "Inspect evidence and reports"]),
    ]
    for col, (number, title, copy, features) in zip(st.columns(3), problem_cards):
        bullets = ''.join(f'<li><span>✓</span>{item}</li>' for item in features)
        with col:
            st.html(f'<article class="problem-panel"><span class="problem-number">{number} &nbsp; / &nbsp; INTELLIGENCE</span><h3>{title}</h3><p>{copy}</p><ul>{bullets}</ul></article>')

    landing_heading("intelligence", "Inside the workspace", "A control tower you can inspect.", "Read-only examples of dashboard analysis, using synthetic data. Navigation and tools are available inside the platform.")
    dashboard_preview()

    landing_heading("architecture", "How it works", "From source data to a decision-ready view.", "A clear path keeps operational records, model outputs and analyst actions connected.")
    flow(["Operational Data", "Feature Engineering", "Trained ML", "Scored Outputs", "Analytics", "AI Copilot", "Decision Support"])
    st.html('<div class="architecture-note"><span>◈</span><p>SupplyChain AI is designed to operationalize verified model outputs inside a traceable decision-intelligence experience. This public preview uses synthetic interface data; model artifacts are not loaded.</p></div>')

    with st.container(key="landing_copilot_section"):
        left, right = st.columns([.88, 1.12], gap="large", vertical_alignment="center")
        with left:
            st.html('<section class="copilot-copy" id="copilot"><span class="dark-eyebrow">SupplyChain AI Copilot</span><h2>Ask your supply chain questions in natural language.</h2><p>Explore operational risk, compare markets, review forecast error and find the evidence behind a model signal—all in the context of your current workspace.</p><div class="prompt-chips"><span>“What changed?”</span><span>“Show high-risk orders.”</span><span>“Compare Europe and LATAM.”</span><span>“Explain this prediction.”</span><span>“Which products have the largest forecast error?”</span></div><small>Example shown below. Inside the platform, use local analytics or optional live OpenAI insights with your configured API key.</small></section>')
        with right:
            st.html(f'''<section class="copilot-preview" role="figure" aria-label="Read-only Copilot answer example"><div class="copilot-preview-head"><div class="copilot-avatar">✧</div><div><b>SupplyChain Copilot</b><small>Read-only answer example</small></div><span class="demo-pill">DEMO</span></div><div class="preview-bubble user-bubble"><span>Example question</span><p>“{LANDING_DEMO['copilot_question']}”</p></div><div class="preview-answer"><span>SupplyChain AI · Demo response</span><p>{LANDING_DEMO['copilot_answer']}</p><div class="response-metric"><div><small>{LANDING_DEMO['copilot_metric_label']}</small><b>{LANDING_DEMO['delivery_risk']}</b></div><span>{LANDING_DEMO['copilot_preview_badge']}</span></div><div class="evidence-preview"><span>▤</span><div><b>Evidence &amp; context</b><small>{LANDING_DEMO['evidence']}</small></div><span class="evidence-check">✓</span></div><p class="preview-summary">Read-only answer example. Investigate records and apply filters inside the platform.</p></div></section>''')
            action, section_link = st.columns([1.15, 1], gap="small")
            action.link_button("See analysis examples", "#intelligence", width="stretch")
            section_link.link_button("Explore Copilot", "#capabilities", width="stretch")

    landing_heading("governance", "Trust through context", "Intelligence you can inspect.", "Each model-backed result is designed to remain traceable to its dataset, selected records, filters, metric and model context.")
    trust_cards = [
        ("▤", "Evidence-backed answers", "See the dataset, filter context, record count and calculation behind an analytical response."),
        ("≋", "Model explainability", "Make model behavior easier to inspect, while keeping feature contribution separate from causality."),
        ("✓", "Data quality", "Understand schema, completeness, coverage and lineage alongside the analysis."),
        ("♡", "Model health", "See capability status and artifact readiness at a glance. Unavailable signals stay visibly unavailable."),
    ]
    for col, item in zip(st.columns(4), trust_cards):
        with col:
            capability_card(*item)

    landing_heading("capabilities", "A connected analytical toolkit", "One workspace. Every next question.", "Move from an executive signal to a focused analysis without losing operational context.")
    for col, (group, start) in zip(st.columns(3), [("Operations", 0), ("Investigation", 4), ("Governance & reports", 8)]):
        with col:
            st.html(f'<h3 class="capability-group-title">{group}</h3>')
            for index in range(start, start + 4):
                with st.container(key=f"landing_capability_{index}"):
                    capability_card(*CAPABILITIES[index], heading_level=4)

    with st.container(key="landing_final_cta"):
        st.html('<section class="final-cta"><span class="dark-eyebrow">SUPPLYCHAIN AI · DECISION INTELLIGENCE</span><h2>Turn predictions into decisions.</h2><p>Enter a unified workspace for delivery intelligence, demand forecasting, operational investigation and evidence-led analysis.</p></section>')
        final_open, final_signin = st.columns([1.3, .9])
        final_open.button("Start an analysis", key="final_launch", type="secondary", icon=":material/arrow_outward:", on_click=enter_demo, width="stretch")
        final_signin.button("Sign in", key="final_signin", on_click=go, args=("login",), width="stretch")

    st.html('<footer class="public-footer"><a class="footer-brand" href="#top"><span class="brand-symbol">' + MARK + '</span><span>SUPPLYCHAIN AI<small>Decision Intelligence Platform</small></span></a><div class="footer-group"><b>PLATFORM</b><a href="#platform">Executive Overview</a><a href="#intelligence">Delivery Intelligence</a><a href="#intelligence">Demand Intelligence</a><a href="#copilot">Copilot</a></div><div class="footer-group"><b>GOVERNANCE</b><a href="#governance">Models</a><a href="#governance">Explainability</a><a href="#governance">Data Quality</a><a href="#governance">Model Health</a></div><div class="footer-group"><b>PROJECT</b><a href="#architecture">Architecture</a><a href="#capabilities">Documentation</a><a href="#top">About</a></div></footer><div class="footer-bottom"><span>Academic / Portfolio Decision Intelligence Platform</span><span>DEMO UI · No operational data · No external AI provider</span></div>')
