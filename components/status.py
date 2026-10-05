from html import escape
import streamlit as st


def badge(text, tone="info"):
    return f'<span class="badge badge-{escape(tone)}">{escape(str(text))}</span>'


def demo_notice(label="DEMO UI DATA · synthetic planning records"):
    st.html(f'<div class="demo-notice"><span class="status-dot"></span><b>Demo UI Mode</b><span>{escape(label)} · no live model inference</span></div>')


def artifact_notice(label):
    st.html(f'<div class="demo-notice"><span class="status-dot"></span><b>REAL DATA · Verified repository snapshot</b><span>{escape(label)} · historical analytics; trained predictions run on request</span></div>')
