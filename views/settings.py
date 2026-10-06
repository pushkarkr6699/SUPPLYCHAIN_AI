import streamlit as st
from components.section_header import section
from services.provider import get_service


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
            st.toggle("Interface animations", key="animation", help="Applies across landing, login and workspace. Your device reduced-motion preference always takes priority.")
        elif active == "Dashboard":
            section("Dashboard", "Tune chart and table defaults")
            st.toggle("Chart value labels", key="labels")
            st.toggle("Chart gridlines", key="gridlines")
            st.toggle("Compact numbers", key="compact_numbers")
            st.selectbox("Table page size", [10, 15, 25, 50], key="page_size")
        elif active == "Data":
            service = get_service()
            section("Data", "Synthetic demo fixtures" if service.demo else "Verified historical repository snapshot")
            st.selectbox("Default date range (days)", [7, 14, 28, 56, 3650], key="default_days", format_func=lambda value: "All available history" if value == 3650 else str(value))
            st.caption("Applied when the workspace date filter is reset.")
            st.info("Synthetic data is selected." if service.demo else "Supplied delivery and web-visit datasets are connected. Profitability line-item data is also connected. This is a historical snapshot; it is not a refreshed operational feed.")
        elif active == "Copilot":
            section("Copilot", "Local analysis and optional live AI configuration")
            st.toggle("Enable Copilot", key="copilot_enabled")
            st.write("**Provider status:** " + ("Synthetic demo" if get_service().demo else "Verified repository analytics"))
            from services import ai_narration
            state=ai_narration.status()
            st.write("**Live AI provider:**",state['provider'])
            st.write("**Live AI model:**",state['model'])
            st.info(state['reason'])
            st.caption("Configure HF_TOKEN and optional HF_MODEL in the ignored local .env. Your key stays server-side. Explicit AI actions send your question and anonymized aggregate evidence.")
            if st.button("Check live AI connection",key="check_live_ai",disabled=not state['available']):
                try:
                    with st.spinner("Checking the configured API connection?"):
                        ai_narration.narrate({'source':'Connection test; no dataset sent','evidence':[{'id':'E1','kind':'Connection check','metric':'Test records','value':0,'segment':None}],'focus':'Confirm this is a connection test with no data.'})
                    st.success("Live AI connection succeeded.")
                except ai_narration.NarrationUnavailable as exc: st.error(str(exc))
        else:
            section("Developer", "Runtime diagnostics and non-sensitive context")
            st.caption("Enabling Developer mode adds runtime and integration diagnostics to the sidebar.")
        st.success("Preferences are saved for this session and cleared on logout.")


def sync_theme():
    st.session_state.theme = st.session_state.settings_theme
