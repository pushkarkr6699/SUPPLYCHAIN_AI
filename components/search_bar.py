import streamlit as st
from components.navigation import go


def search_bar():
    with st.form("global_search_form", border=False):
        cols = st.columns([5, 1])
        value = cols[0].text_input("Universal search", placeholder="Search orders, products, markets…", label_visibility="collapsed")
        if cols[1].form_submit_button("Search", icon=":material/search:"):
            go("explorer", search_query=value)
            st.rerun()

