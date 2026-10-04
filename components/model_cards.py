from html import escape
import streamlit as st
from services.provider import get_service
from components.status import badge


def model_cards():
    cols = st.columns(4)
    for col, model in zip(cols, get_service().model_status()):
        with col:
            st.html(f'<div class="model-card"><h3>{escape(model["Model"])} model</h3>{badge(model["Status"], "neutral" if model["Model"] == "Profitability" else "info")}<p>{escape(model["Capability"])}</p></div>')
    with cols[-1]:
        st.html(f'<div class="model-card"><h3>Data quality</h3>{badge("Synthetic fixtures", "info")}<p>Measured on demo records. Production data is not connected.</p></div>')

