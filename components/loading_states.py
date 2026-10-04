import streamlit as st


def skeletons(count=3):
    for col in st.columns(count):
        with col:
            st.html('<div class="disabled-panel" role="status" aria-label="Loading"><div class="skeleton short"></div><div class="skeleton"></div><div class="skeleton"></div></div>')

