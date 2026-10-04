import streamlit as st
from services.provider import get_service


def evidence(df, filters=None, calculation=None):
    with st.expander("Evidence & provenance", icon=":material/fact_check:"):
        context = get_service().evidence(df, filters if filters is not None else st.session_state.get("filters", {}))
        if calculation:
            context["Metric / calculation"] = calculation
        for name, value in context.items():
            st.write(f"**{name}**", value)

