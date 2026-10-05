from html import escape
import streamlit as st


def section(title, subtitle=None, tag=None, *, level=3):
    if level not in (2, 3, 4):
        raise ValueError("Section headings must use level 2, 3 or 4")
    st.html(f'<div class="section-heading"><div><h{level}>{escape(title)}</h{level}>{"<p>" + escape(subtitle) + "</p>" if subtitle else ""}</div>{"<span class=eyebrow>" + escape(tag) + "</span>" if tag else ""}</div>')


def page_title(title, subtitle):
    st.html(f'<div class="page-heading"><div class="eyebrow">ANALYTICS WORKSPACE</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>')

