from html import escape
import streamlit as st
from components.status import badge


def empty_state(title="No matching records", description="Adjust your filters or reset the view to continue.", status="Data unavailable"):
    st.html(f'<div class="empty-state"><div class="empty-icon">◇</div>{badge(status, "neutral")}<h2>{escape(title)}</h2><p>{escape(description)}</p></div>')


def disabled_panels(titles):
    cols = st.columns(3)
    for i, title in enumerate(titles):
        with cols[i % 3]:
            st.html(f'<div class="disabled-panel"><span class="eyebrow">NOT CONNECTED</span><h3>{escape(title)}</h3><div class="skeleton"></div><div class="skeleton short"></div><p>Available after verified artifact connection</p></div>')

