import streamlit as st
from components.breadcrumbs import breadcrumbs
from components.navigation import ROUTES, go
from components.presentation import toggle_presentation, presentation_banner
from components.search_bar import search_bar
from services.auth_service import logout


def header():
    label, group, _ = ROUTES.get(st.session_state.route, ROUTES["overview"])
    with st.container(key="top_header"):
        left, right = st.columns([1.1, 1.5])
        with left:
            breadcrumbs(group, label)
        with right:
            cols = st.columns([3.4, 1, 1, 1, 1, 1])
            with cols[0]:
                with st.popover("Search", icon=":material/search:", width="stretch"):
                    search_bar()
            cols[1].button("", icon=":material/fullscreen_exit:" if st.session_state.presentation else ":material/fullscreen:", help="Toggle presentation mode", key="presentation_button", on_click=toggle_presentation)
            with cols[2]:
                with st.popover("", icon=":material/contrast:", help="Appearance"):
                    st.radio("Theme", ["Light", "Dark", "System"], key="theme")
            cols[3].button("", icon=":material/notifications:", help="Open alert center", on_click=go, args=("alerts",), key="header_alerts")
            if cols[4].button("", icon=":material/auto_awesome:", help="Toggle Copilot context drawer", disabled=not st.session_state.copilot_enabled, key="header_copilot"):
                st.session_state.copilot_open = not st.session_state.copilot_open
                st.rerun()
            with cols[5]:
                with st.popover("", icon=":material/account_circle:", help="User menu"):
                    st.write(st.session_state.user_name)
                    st.caption("Temporary demo session")
                    st.button("Settings", on_click=go, args=("settings",), key="user_settings")
                    st.button("Sign out", on_click=logout)
    presentation_banner()

