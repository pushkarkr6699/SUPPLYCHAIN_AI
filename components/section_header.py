from html import escape
import streamlit as st


def section(title, subtitle=None, tag=None):
    st.html(f'<div class="section-heading"><div><h3>{escape(title)}</h3>{"<p>" + escape(subtitle) + "</p>" if subtitle else ""}</div>{"<span class=eyebrow>" + escape(tag) + "</span>" if tag else ""}</div>')


def page_title(title, subtitle):
    st.html(f'<div class="page-heading"><div class="eyebrow">ANALYTICS WORKSPACE</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>')

