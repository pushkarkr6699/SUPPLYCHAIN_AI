from html import escape
import base64
import re
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


CAPABILITY_ICONS = [
    '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    '<path d="M3 6h11v11H3zM14 10h4l3 4v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
    '<path d="M3 3v18h18M6 16l5-6 4 3 6-8"/>',
    '<path d="M5 5h14v16H5zM8 3h8v4H8M8 11h8M8 15h5"/>',
    '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
    '<path d="M9 3v6l-5 9q-1 3 2 3h12q3 0 2-3l-5-9V3M8 3h8M7 15h10"/>',
    '<path d="M8 16a6 6 0 1 1 8 0l-1 3H9zM9 22h6"/>',
    '<path d="M12 3L2 21h20zM12 9v5M12 17v1"/>',
    '<rect x="7" y="7" width="10" height="10"/><path d="M3 9h4M3 15h4M17 9h4M17 15h4M9 3v4M15 3v4M9 17v4M15 17v4"/>',
    '<path d="M4 5h16M4 12h16M4 19h16"/><circle cx="8" cy="5" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="11" cy="19" r="2"/>',
    '<path d="M12 3l8 3v6q0 6-8 9-8-3-8-9V6zM8 12l3 3 5-6"/>',
    '<path d="M5 3h10l4 4v14H5zM15 3v5h4M8 12h8M8 16h6"/>',
]


def public_html(markup):
    """Keep static SVG assets visible under Streamlit's HTML-only sanitization."""
    def image_svg(match):
        attrs, drawing = match.groups()
        class_match = re.search(r'class="([^"]*)"', attrs)
        label_match = re.search(r'aria-label="([^"]*)"', attrs)
        viewbox = re.search(r'viewBox="([^"]*)"', attrs)
        styles = '.spark-grid{fill:none;stroke:#e3e9f2;stroke-width:1}.spark-fill{fill:#496fe114}.hero-series{fill:none;stroke:#496fe1;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox[1] if viewbox else "0 0 24 24"}" fill="none" stroke="#315de6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><style>{styles}</style>{drawing}</svg>'
        encoded = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        cls = escape(class_match[1], quote=True) if class_match else 'capability-icon'
        alt = escape(label_match[1], quote=True) if label_match else ''
        return f'<img class="{cls}" alt="{alt}" src="data:image/svg+xml;base64,{encoded}" />'
    st.html(re.sub(r'<svg([^>]*)>(.*?)</svg>', image_svg, markup, flags=re.DOTALL))


def capability_card(icon, title, copy, index=None, heading_level=3):
    if index:
        drawing = CAPABILITY_ICONS[int(index) - 1]
        label = f'<div class="capability-card-head"><span class="cap-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">{drawing}</svg></span><span class="cap-index" aria-hidden="true">{escape(index)}</span></div>'
    else:
        label = f'<span class="cap-icon" aria-hidden="true">{escape(icon)}</span>'
    heading = "h4" if heading_level == 4 else "h3"
    public_html(f'<article class="capability-card">{label}<{heading}>{escape(title)}</{heading}><p>{escape(copy)}</p></article>')


def landing_heading(anchor, eyebrow, title, copy=""):
    st.html(f'<div class="landing-section" id="{escape(anchor)}"><span class="eyebrow">{escape(eyebrow)}</span><h2>{escape(title)}</h2><p>{escape(copy)}</p></div>')


def dashboard_preview():
    values = LANDING_DEMO["risk_points"]
    points = " ".join(f"{24 + i * 33},{110 - value}" for i, value in enumerate(values))
    circles = "".join(f'<circle cx="{24 + i * 33}" cy="{110 - value}" r="2.3"/>' for i, value in enumerate(values))
    distribution = "".join(f'<div class="preview-band"><span><i class="band-dot {slug(label)}"></i>{escape(label)}</span><b>{value}%</b></div>' for label, value in LANDING_DEMO["risk_distribution"])
    records = "".join(f'<div class="preview-record"><span>{escape(order)}<small>{escape(market)}</small></span><b>{escape(score)}</b><em class="risk-{slug(level)}">{escape(level)}</em></div>' for order, market, score, level in LANDING_DEMO["critical_records"])
    public_html(f'''<section class="tower-preview" role="figure" aria-labelledby="tower-preview-title" aria-describedby="tower-preview-caption">
      <div class="tower-body">
       <div class="tower-main"><div class="tower-page-title"><div><span>Executive command center</span><h3 id="tower-preview-title">Operations at a glance</h3></div><span class="demo-pill">DEMO UI DATA</span></div>
        <div class="tower-kpis"><article><span>High-risk delivery</span><b>{LANDING_DEMO['delivery_risk']}</b><small>Demo records in a high-risk band</small></article><article><span>Forecast demand</span><b>{LANDING_DEMO['forecast_units']}</b><small>Illustrative planning units</small></article><article><span>Next-day outlook</span><b class="growth">{LANDING_DEMO['demand_change']}</b><small>Demo comparison signal</small></article></div>
        <div class="tower-charts"><section class="tower-chart-card"><div class="tower-card-heading"><div><b>Demand forecast</b><small>Illustrative daily series · DEMO</small></div><span>28 DAYS</span></div><svg class="demand-svg" viewBox="0 0 550 126" role="img" aria-label="Illustrative demo demand forecast line chart"><defs><linearGradient id="demoFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4d77eb" stop-opacity=".20"/><stop offset="1" stop-color="#4d77eb" stop-opacity="0"/></linearGradient></defs><path d="M20 112 H530 M20 78 H530 M20 44 H530 M20 10 H530" fill="none" stroke="#e8edf5" stroke-width="1"/><path d="M24 108 L57 94 L90 99 L123 77 L156 84 L189 68 L222 76 L255 50 L288 59 L321 44 L354 51 L387 34 L420 43 L453 22 L486 31 L519 9 L519 112 L24 112Z" fill="url(#demoFill)"/><polyline points="{points}" fill="none" stroke="#496fe1" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>{circles}</svg><div class="tower-axis"><span>12 SEP</span><span>19 SEP</span><span>26 SEP</span><span>04 OCT</span></div></section>
        <section class="tower-chart-card risk-card"><div class="tower-card-heading"><div><b>Delivery risk bands</b><small>Share of demo records</small></div><span>DEMO</span></div><div class="risk-ring"><div><b>{LANDING_DEMO['orders']}</b><small>Demo orders</small></div></div><div class="risk-legend">{distribution}</div></section></div>
        <section class="tower-records"><div class="tower-card-heading"><div><b>Critical records</b><small>Illustrative order review</small></div><span class="critical-count">03 SIGNALS</span></div><div class="tower-record-head"><span>Order / market</span><span>RISK</span><span>LEVEL</span></div>{records}</section>
       </div><aside class="tower-copilot" aria-label="Example Copilot answer"><div class="copilot-heading"><span>✧</span><div><b>SupplyChain Copilot</b><small>Analytical preview</small></div><i></i></div><div class="copilot-thread"><small>Example question</small><div class="copilot-question">“{escape(LANDING_DEMO['copilot_question'])}”</div><small>SUPPLYCHAIN AI</small><p>{escape(LANDING_DEMO['copilot_answer'])}</p><div class="copilot-metric"><span>High-risk demo records</span><b>{LANDING_DEMO['delivery_risk']}</b></div><div class="copilot-evidence"><b>▤ &nbsp; Evidence</b><span>{escape(LANDING_DEMO['evidence'])}</span></div></div><p class="preview-summary">Read-only answer example. Open the platform to investigate records and evidence.</p></aside></div>
      <div class="tower-footnote" id="tower-preview-caption">Read-only example · Interface preview · Synthetic values for design purposes · Delivery and demand artifacts are not loaded in this public preview</div>
     </section>''')


def hero_preview():
    points = " ".join(f"{4 + index * (422 / (len(LANDING_DEMO['risk_points']) - 1)):.1f},{104 - value * .78:.1f}" for index, value in enumerate(LANDING_DEMO["risk_points"]))
    delivery_status = escape(LANDING_DEMO["delivery_model"])
    demand_status = escape(LANDING_DEMO["demand_model"])
    public_html(f'''<div class="hero-surface" aria-label="SupplyChain AI dashboard preview"><div class="hero-surface-header"><span><i class="hero-surface-dot"></i> Operations workspace</span><span class="demo-pill">DEMO UI DATA</span></div><div class="hero-surface-kpis"><article><span>High-risk delivery</span><b>{escape(LANDING_DEMO['delivery_risk'])}</b><small>{escape(LANDING_DEMO['delivery_caption'])}</small></article><article><span>Demand outlook</span><b class="hero-growth">{escape(LANDING_DEMO['demand_change'])}</b><small>{escape(LANDING_DEMO['demand_caption'])}</small></article></div><div class="hero-line-head"><b>Demand forecast</b><span>Read-only example</span></div><svg class="hero-spark" viewBox="0 0 430 116" role="img" aria-label="Illustrative demo demand forecast chart"><path class="spark-grid" d="M4 18H426M4 48H426M4 78H426M4 108H426"/><path class="spark-fill" d="M4 96 L40 82 L76 89 L112 62 L148 72 L184 50 L220 58 L256 38 L292 51 L328 26 L364 39 L400 15 L426 23 V112 H4Z"/><polyline class="hero-series" points="{points}"/></svg><div class="hero-surface-foot"><span>Model status · Demo</span><b>Delivery <i>{delivery_status}</i></b><b>Demand <i>{demand_status}</i></b></div></div>''')


def slug(value):
    return value.lower().replace(" ", "-")


def flow(stages):
    pieces = []
    for index, stage in enumerate(stages):
        pieces.append(f'<div class="flow-stage"><span>{index + 1:02}</span><b>{escape(stage)}</b></div>')
    st.html('<div class="flow">' + '<span class="flow-arrow" aria-hidden="true">→</span>'.join(pieces) + '</div>')

