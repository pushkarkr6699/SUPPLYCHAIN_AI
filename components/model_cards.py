from html import escape
import streamlit as st
from services.provider import get_service
from components.status import badge


def model_cards():
    service = get_service()
    models = service.model_status()
    cols = st.columns(3)
    for index, model in enumerate(models):
        col = cols[index % 3]
        with col:
            name = model.get("Model", model.get("Capability", "Model"))
            description = model.get("Capability", model.get("Source", "Supplied artifact"))
            st.html(f'<div class="model-card"><h3>{escape(name)}</h3>{badge(model["Status"], "neutral" if name == "Profitability" else "info")}<p>{escape(description)}</p></div>')
    with cols[len(models) % 3]:
        label = "Synthetic fixtures" if service.demo else "Supplied artifacts"
        description = "Measured on demo records. Production data is not connected." if service.demo else "Measured on loaded data. Score coverage and missing values remain visible."
        st.html(f'<div class="model-card"><h3>Data quality</h3>{badge(label, "info")}<p>{description}</p></div>')

