import streamlit as st
from components.navigation import go
from services.copilot.validation import validate_filter, validate_route


def navigate_to_page(route):
    go(validate_route(route))


def apply_filter(df, column, values):
    column, values = validate_filter(df, column, values)
    st.session_state.filters[column] = values
    st.session_state.pop(f"filter_{column}", None)


def apply_high_risk(df):
    apply_filter(df, "Risk", [value for value in ("High", "Critical") if value in set(df.Risk)])
    navigate_to_page("delivery")
