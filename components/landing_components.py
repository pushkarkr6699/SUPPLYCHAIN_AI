from html import escape
import streamlit as st
from services.mock_data import LANDING_DEMO

CAPABILITIES = [
    ("01", "Executive Command Center", "A focused view of delivery signals, demand and workspace readiness.", "01"),
    ("02", "Delivery Intelligence", "Inspect delivery probabilities, risk bands and critical orders.", "02"),
    ("03", "Demand Intelligence", "Review next-day forecasts, uncertainty and demand movement.", "03"),
    ("04", "Order Explorer", "Follow an operational signal through to an individual case file.", "04"),
    ("05", "Geographic Intelligence", "Compare delivery and demand indicators across markets.", "05"),
    ("06", "Scenario Lab", "Explore supported model scenarios in a distinct workspace.", "06"),
    ("07", "Insight Center", "Review deterministic observations alongside evidence.", "07"),
    ("08", "Alert Center", "Triage critical, attention and information signals.", "08"),
    ("09", "Model Intelligence", "Inspect model context, coverage and validation readiness.", "09"),
    ("10", "Explainability", "Explore model contributions and their limits.", "10"),
    ("11", "Data Governance", "Trace schema, quality, lineage and provenance.", "11"),
    ("12", "Reporting", "Package a filtered analytical view for review.", "12"),
]


def capability_card(icon, title, copy, index=None):
    label = f'<span class="cap-index">{escape(index)}</span>' if index else f'<span class="cap-icon">{escape(icon)}</span>'
    st.html(f'<article class="capability-card">{label}<h3>{escape(title)}</h3><p>{escape(copy)}</p></article>')


def landing_heading(anchor, eyebrow, title, copy=""):
    st.html(f'<div class="landing-section" id="{escape(anchor)}"><span class="eyebrow">{escape(eyebrow)}</span><h2>{escape(title)}</h2><p>{escape(copy)}</p></div>')


def dashboard_preview():
    values = LANDING_DEMO["risk_points"]
    points = " ".join(f"{24 + i * 33},{110 - value}" for i, value in enumerate(values))
    circles = "".join(f'<circle cx="{24 + i * 33}" cy="{110 - value}" r="2.3"/>' for i, value in enumerate(values))
    distribution = "".join(f'<div class="preview-band"><span><i class="band-dot {slug(label)}"></i>{escape(label)}</span><b>{value}%</b></div>' for label, value in LANDING_DEMO["risk_distribution"])
    records = "".join(f'<div class="preview-record"><span>{escape(order)}<small>{escape(market)}</small></span><b>{escape(score)}</b><em class="risk-{slug(level)}">{escape(level)}</em></div>' for order, market, score, level in LANDING_DEMO["critical_records"])
    st.html(f'''<section class="tower-preview" aria-label="SupplyChain AI control tower preview">
      <div class="tower-top"><div><span class="tower-window"><i></i><i></i><i></i></span><b>SUPPLYCHAIN <span>AI</span></b><small>DECISION INTELLIGENCE</small></div><span class="preview-live"><i></i> PRODUCT PREVIEW</span></div>
      <div class="tower-body"><aside class="tower-nav"><div class="tower-workspace">◈ &nbsp; Operations workspace</div><div class="tower-section-label">COMMAND CENTER</div><div class="tower-nav-item selected">▦ &nbsp; Executive overview</div><div class="tower-section-label">INTELLIGENCE</div><div class="tower-nav-item">↗ &nbsp; Delivery</div><div class="tower-nav-item">⌁ &nbsp; Demand</div><div class="tower-nav-item">◎ &nbsp; Risk signals</div><div class="tower-section-label">GOVERNANCE</div><div class="tower-nav-item">≋ &nbsp; Model health</div><div class="tower-nav-item">✧ &nbsp; Copilot</div></aside>
       <main class="tower-main"><div class="tower-page-title"><div><span>EXECUTIVE COMMAND CENTER</span><h3>Operations at a glance</h3></div><span class="demo-pill">DEMO UI DATA</span></div>
        <div class="tower-kpis"><article><span>HIGH-RISK DELIVERY</span><b>{LANDING_DEMO['delivery_risk']}</b><small>Demo records in a high-risk band</small></article><article><span>FORECAST DEMAND</span><b>{LANDING_DEMO['forecast_units']}</b><small>Illustrative planning units</small></article><article><span>NEXT-DAY OUTLOOK</span><b class="growth">{LANDING_DEMO['demand_change']}</b><small>Demo comparison signal</small></article></div>
        <div class="tower-charts"><section class="tower-chart-card"><div class="tower-card-heading"><div><b>Demand forecast</b><small>Illustrative daily series · DEMO</small></div><span>28 DAYS</span></div><svg class="demand-svg" viewBox="0 0 550 126" role="img" aria-label="Illustrative demo demand forecast line chart"><defs><linearGradient id="demoFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4d77eb" stop-opacity=".20"/><stop offset="1" stop-color="#4d77eb" stop-opacity="0"/></linearGradient></defs><path d="M20 112 H530 M20 78 H530 M20 44 H530 M20 10 H530" fill="none" stroke="#e8edf5" stroke-width="1"/><path d="M24 108 L57 94 L90 99 L123 77 L156 84 L189 68 L222 76 L255 50 L288 59 L321 44 L354 51 L387 34 L420 43 L453 22 L486 31 L519 9 L519 112 L24 112Z" fill="url(#demoFill)"/><polyline points="{points}" fill="none" stroke="#496fe1" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>{circles}</svg><div class="tower-axis"><span>12 SEP</span><span>19 SEP</span><span>26 SEP</span><span>04 OCT</span></div></section>
        <section class="tower-chart-card risk-card"><div class="tower-card-heading"><div><b>Delivery risk bands</b><small>Share of demo records</small></div><span>DEMO</span></div><div class="risk-ring"><div><b>{LANDING_DEMO['orders']}</b><small>DEMO ORDERS</small></div></div><div class="risk-legend">{distribution}</div></section></div>
        <section class="tower-records"><div class="tower-card-heading"><div><b>Critical records</b><small>Illustrative order review</small></div><span class="critical-count">03 SIGNALS</span></div><div class="tower-record-head"><span>ORDER / MARKET</span><span>RISK</span><span>LEVEL</span></div>{records}</section>
       </main><aside class="tower-copilot"><div class="copilot-heading"><span>✧</span><div><b>SupplyChain Copilot</b><small>ANALYTICAL PREVIEW</small></div><i></i></div><div class="copilot-thread"><small>YOU ASKED</small><div class="copilot-question">“{escape(LANDING_DEMO['copilot_question'])}”</div><small>SUPPLYCHAIN AI</small><p>{escape(LANDING_DEMO['copilot_answer'])}</p><div class="copilot-metric"><span>HIGH-RISK DEMO RECORDS</span><b>{LANDING_DEMO['delivery_risk']}</b></div><div class="copilot-evidence"><b>▤ &nbsp; Evidence</b><span>{escape(LANDING_DEMO['evidence'])}</span></div></div><div class="copilot-actions"><span>View in dashboard</span><span>Open evidence ↗</span></div></aside></div>
      <div class="tower-footnote">Interface preview · Synthetic values for design purposes · Delivery and demand artifacts are not loaded in this public preview</div>
     </section>''')


def hero_preview():
    points = " ".join(f"{4 + index * (422 / (len(LANDING_DEMO['risk_points']) - 1)):.1f},{104 - value * .78:.1f}" for index, value in enumerate(LANDING_DEMO["risk_points"]))
    delivery_status = escape(LANDING_DEMO["delivery_model"])
    demand_status = escape(LANDING_DEMO["demand_model"])
    st.html(f'''<div class="hero-surface" aria-label="SupplyChain AI dashboard preview"><div class="hero-surface-header"><span><i class="hero-surface-dot"></i> OPERATIONS WORKSPACE</span><span class="demo-pill">DEMO UI DATA</span></div><div class="hero-surface-kpis"><article><span>HIGH-RISK DELIVERY</span><b>{escape(LANDING_DEMO['delivery_risk'])}</b><small>{escape(LANDING_DEMO['delivery_caption'])}</small></article><article><span>DEMAND OUTLOOK</span><b class="hero-growth">{escape(LANDING_DEMO['demand_change'])}</b><small>{escape(LANDING_DEMO['demand_caption'])}</small></article></div><div class="hero-line-head"><b>Demand forecast</b><span>INTERFACE PREVIEW</span></div><svg class="hero-spark" viewBox="0 0 430 116" role="img" aria-label="Illustrative demo demand forecast chart"><path class="spark-grid" d="M4 18H426M4 48H426M4 78H426M4 108H426"/><path class="spark-fill" d="M4 96 L40 82 L76 89 L112 62 L148 72 L184 50 L220 58 L256 38 L292 51 L328 26 L364 39 L400 15 L426 23 V112 H4Z"/><polyline class="hero-series" points="{points}"/></svg><div class="hero-surface-foot"><span>MODEL STATUS · DEMO</span><b>Delivery <i>{delivery_status}</i></b><b>Demand <i>{demand_status}</i></b></div></div>''')


def slug(value):
    return value.lower().replace(" ", "-")


def flow(stages):
    pieces = []
    for index, stage in enumerate(stages):
        pieces.append(f'<div class="flow-stage"><span>{index + 1:02}</span><b>{escape(stage)}</b></div>')
    st.html('<div class="flow">' + '<span class="flow-arrow" aria-hidden="true">→</span>'.join(pieces) + '</div>')

