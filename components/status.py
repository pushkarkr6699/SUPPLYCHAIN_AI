from html import escape
import streamlit as st


def badge(text, tone="info"):
    return f'<span class="badge badge-{escape(tone)}">{escape(str(text))}</span>'


def demo_notice():
    st.html('<div class="demo-notice"><span class="status-dot"></span><b>Demo UI Mode</b><span>Deterministic synthetic snapshot · no live model inference</span></div>')
