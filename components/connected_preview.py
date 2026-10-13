"""Public, aggregate-only previews built from registered sources."""
from html import escape
import streamlit as st
from components.landing_components import public_html
from services.workspace_status import connected_sources
from services.provider import get_service


def snapshot():
    sources = connected_sources(get_service())
    result = {}
    for key, item in sources.items():
        frame = item['frame']
        result[key] = {k: item[k] for k in ('label', 'available', 'rows', 'period', 'status')}
        if item['available'] and key == 'delivery':
            result[key]['scored'] = int(frame['Risk Probability'].notna().sum())
        if item['available'] and key == 'profitability':
            result[key]['probability'] = float(frame['Profitability Probability'].mean())
        if item['available'] and key == 'demand':
            daily = frame.groupby(frame.Date.dt.normalize())['Forecast Demand'].sum(min_count=1).dropna()
            result[key]['series'] = [float(v) for v in daily.tail(16)]
    return result


def preview(data, detailed=False):
    cards = ''
    for key in ('delivery', 'demand', 'profitability'):
        item = data[key]
        value = f"{item['rows']:,}" if item['available'] else 'Unavailable'
        cards += '<article><span>'+escape(item['label'])+'</span><b>'+value+'</b><small>'+escape(item['period'])+'</small></article>'
    demand = data['demand']
    chart = '<p class="preview-summary">Registered demand source unavailable in this environment.</p>'
    values = demand.get('series', [])
    if len(values) > 1:
        lo, hi = min(values), max(values)
        points = ' '.join(f'{4+i*422/(len(values)-1):.1f},{104-(v-lo)/max(hi-lo,1)*86:.1f}' for i,v in enumerate(values))
        chart = '<div class="hero-line-head"><b>Supplied daily forecast · web visits</b><span>Last '+str(len(values))+' observed days</span></div><svg class="hero-spark" viewBox="0 0 430 116" role="img" aria-label="Registered daily web-visit forecasts"><path class="spark-grid" d="M4 18H426M4 48H426M4 78H426M4 108H426"/><polyline class="hero-series" points="'+points+'"/></svg>'
    delivery = data['delivery']
    coverage = f"{delivery.get('scored',0):,} / {delivery['rows']:,} orders have supplied scores" if delivery['available'] else 'Delivery source unavailable'
    profit = data['profitability']
    probability = f"Mean supplied line probability {profit['probability']:.1%}" if profit['available'] else 'Profitability source unavailable'
    public_html('<section class="hero-surface" aria-label="Registered dataset overview"><div class="hero-surface-header"><span><i class="hero-surface-dot"></i> Connected analytics</span><span class="demo-pill">REGISTERED SOURCES</span></div><div class="hero-surface-kpis">'+cards+'</div>'+chart+'<div class="hero-surface-foot"><span>'+escape(coverage)+'</span></div><p class="preview-summary">'+escape(probability)+' · Historical sources retain independent grains. Counts show complete source coverage.</p></section>')
    if detailed:
        st.caption('Historical source summaries only; no customer fields or individual order records are published here. Interactive filters, models and reports are inside the workspace.')


def answer_preview(data):
    lines = [f"{item['label']}: {item['rows']:,} source records" if item['available'] else item['label']+': source unavailable' for item in data.values()]
    st.html('<section class="copilot-preview"><div class="copilot-preview-head"><div class="copilot-avatar">✧</div><div><b>Sevika · Local analytical summary</b><small>Calculated from registered source files</small></div></div><div class="preview-answer"><p>'+escape('; '.join(lines))+'.</p><p class="preview-summary">Delivery orders, product/day web visits and line observations remain separate. Live AI is optional and depends on provider configuration and credits.</p></div></section>')
