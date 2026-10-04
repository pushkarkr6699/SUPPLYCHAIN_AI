from html import escape
import streamlit as st


def breadcrumbs(group, page):
    st.html(f'<div class="breadcrumbs">Workspace <span>/</span> {escape(group.title())} <span>/</span> <b>{escape(page)}</b></div>')

