from html import escape
import math
import streamlit as st


def number(value, kind="number"):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return "N/A"
    if kind == "percent":
        return f"{value:.1%}" if not isinstance(value, str) else value
    if isinstance(value, str):
        return value
    if st.session_state.get("compact_numbers", True) and abs(value) >= 10000:
        return f"{value / 1000:,.1f}k"
    return f"{value:,.1f}" if kind == "decimal" else f"{value:,.0f}"


def kpis(items):
    """Render shared KPI cards from legacy tuples or expressive mappings.

    Mapping keys: label, value, kind, caption, tone, delta, status, target, tooltip.
    """
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        if isinstance(item, dict):
            label = item.get("label", "Metric")
            value = item.get("value", "—")
            kind = item.get("kind", "number")
            caption = item.get("caption", "")
            tone = item.get("tone", "blue")
            delta = item.get("delta")
            status = item.get("status")
            target = item.get("target")
            tooltip = item.get("tooltip", "")
        else:
            label, value, kind, caption, *tones = item
            tone = tones[0] if tones else "blue"
            delta = tones[1] if len(tones) > 1 else None
            status = tones[2] if len(tones) > 2 else None
            target = tones[3] if len(tones) > 3 else None
            tooltip = tones[4] if len(tones) > 4 else ""
        extras = []
        if delta is not None:
            extras.append(f'<span class="kpi-delta">{escape(str(delta))}</span>')
        if status:
            extras.append(f'<span class="kpi-status">{escape(str(status))}</span>')
        if target is not None:
            extras.append(f'<span class="kpi-target">Target {escape(str(target))}</span>')
        with col:
            st.html(
                f'<div class="kpi-card {escape(str(tone))}" title="{escape(str(tooltip))}">'
                f'<div class="kpi-label">{escape(str(label))}</div>'
                f'<div class="kpi-value">{escape(number(value, kind))}</div>'
                f'<div class="kpi-caption">{escape(str(caption))}</div>'
                f'<div class="kpi-meta">{"".join(extras)}</div></div>'
            )
