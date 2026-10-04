import streamlit as st


def remove_filter(column):
    st.session_state.filters.pop(column, None)
    key = f"filter_{column}"
    if key in st.session_state:
        del st.session_state[key]


def filter_chips():
    active = [(key, value) for key, value in st.session_state.filters.items() if value]
    if not active:
        return
    cols = st.columns(min(len(active), 5))
    for index, (key, values) in enumerate(active):
        if key == "Date" and len(values) == 2:
            label = f"{values[0]:%d %b} – {values[1]:%d %b %Y}"
        else:
            label = ", ".join(str(value) for value in values)
        cols[index % len(cols)].button(f"{key}: {label}  ×", key=f"chip_{key}", on_click=remove_filter, args=(key,))
