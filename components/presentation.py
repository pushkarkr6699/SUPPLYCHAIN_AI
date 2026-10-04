import streamlit as st


def toggle_presentation():
    st.session_state.presentation = not st.session_state.presentation


def presentation_banner():
    if st.session_state.presentation:
        st.html('<div class="presentation-banner">PRESENTATION VIEW <span>Same data. Focused perspective.</span></div>')

