import streamlit as st
from components.section_header import section


def render(df):
    st.session_state.settings_theme = st.session_state.theme
    nav, panel = st.columns([1, 3], gap="large")
    with nav, st.container(border=True):
        section("Settings", "Session preferences")
        active = st.radio("Settings sections", ["Appearance", "Dashboard", "Data", "Copilot", "Developer"], label_visibility="collapsed", key="settings_section")
        st.toggle("Developer mode", key="developer_mode", help="Shows diagnostics navigation; this is not an authorization control")
    with panel:
        if active == "Appearance":
            section("Appearance", "Preferences apply to this browser session")
            st.radio("Theme", ["Light", "Dark", "System"], key="settings_theme", index=["Light", "Dark", "System"].index(st.session_state.theme), on_change=sync_theme, horizontal=True)
            st.radio("Density", ["Comfortable", "Compact"], key="density", horizontal=True)
            st.toggle("Presentation mode", key="presentation")
        elif active == "Dashboard":
            section("Dashboard", "Tune chart and table defaults")
            st.toggle("Chart value labels", key="labels")
            st.toggle("Chart gridlines", key="gridlines")
            st.toggle("Compact numbers", key="compact_numbers")
            st.toggle("Chart transitions", key="animation", help="Reduced-motion preferences take priority")
            st.selectbox("Table page size", [10, 15, 25, 50], key="page_size")
        elif active == "Data":
            section("Data", "Current UI phase uses isolated synthetic fixtures")
            st.selectbox("Default date range (days)", [7, 14, 28, 56], key="default_days")
            st.caption("Applied when the workspace date filter is reset. No operational data source is connected.")
            st.info("Data is synthetic and excludes personal customer details. No secrets or credentials are displayed.")
        elif active == "Copilot":
            section("Copilot", "Offline assistant configuration")
            st.toggle("Enable Copilot", key="copilot_enabled")
            st.write("**Provider status:** Offline preview")
            st.write("**Model status:** No LLM connected")
            st.caption("Responses use the isolated mock service. No prompt is sent to an external provider.")
        else:
            section("Developer", "Runtime diagnostics and non-sensitive context")
            st.caption("Enabling Developer mode adds runtime and integration diagnostics to the sidebar.")
        st.success("Preferences are saved for this session and cleared on logout.")


def sync_theme():
    st.session_state.theme = st.session_state.settings_theme
