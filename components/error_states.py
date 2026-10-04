import logging
import streamlit as st


def service_error(error):
    logging.getLogger(__name__).error("Service failure: %s", type(error).__name__)
    st.error("The data service is unavailable. Your view settings have been preserved. Retry or open Model Health.")
    if st.button("Retry data service"):
        st.rerun()


def page_error(route):
    """Keep implementation details in server logs and show a recoverable UI state."""
    logging.getLogger(__name__).exception("Page render failed: %s", route)
    st.error("This page could not be rendered. Your filters and workspace settings are still available.")
    left, right = st.columns(2)
    if left.button("Retry page", key=f"retry_page_{route}"):
        st.rerun()
    if right.button("Open Model Health", key=f"health_page_{route}"):
        st.session_state.route = "health"
        st.rerun()

