import streamlit as st


def remove_filter(column):
    st.session_state.filters.pop(column, None)
    if column == "Date":
        st.session_state.date_reset_revision = st.session_state.get("date_reset_revision", 0) + 1
    for key in list(st.session_state):
        if key == f"filter_{column}" or key.startswith(f"filter_{column}_"):
            del st.session_state[key]


def filter_chips():
    active = [(key, value) for key, value in st.session_state.filters.items() if value]
    if not active:
        return
    cols = st.columns(min(len(active), 5))
    for index, (key, values) in enumerate(active):
        if key == "Date" and len(values) == 2:
            start_format = "%d %b %Y" if values[0].year != values[1].year else "%d %b"
            label = f"{values[0].strftime(start_format)} – {values[1]:%d %b %Y}"
        else:
            label = ", ".join(str(value) for value in values)
        cols[index % len(cols)].button(f"{key}: {label}  ×", key=f"chip_{key}", on_click=remove_filter, args=(key,))
