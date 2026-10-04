from copy import deepcopy
from datetime import datetime
from time import perf_counter
import streamlit as st
from config import ROOT, DEFAULTS
from components.sidebar import sidebar
from components.header import header
from components.filters import filters
from components.status import demo_notice
from components.section_header import page_title
from components.evidence import evidence
from components.empty_states import empty_state
from components.error_states import service_error, page_error
from components.copilot_ui import context_drawer
from components.navigation import nav_button
from views.registry import PAGES


def initialize():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)
        else:
            # Detach durable preferences from page-local widget cleanup.
            st.session_state[key] = st.session_state[key]
    if "route_initialized" not in st.session_state:
        route = st.query_params.get("page", st.session_state.route)
        st.session_state.route = route if route in PAGES or route in ["landing", "login"] else "landing"
        st.session_state.route_initialized = True


def load_styles():
    content = "\n".join((ROOT / "styles" / name).read_text(encoding="utf-8") for name in ["theme.css", "layout.css", "components.css", "landing.css", "auth.css", "dashboard.css", "presentation.css"])
    dark = ':root{--bg:#0e192b;--surface:#16243a;--surface-alt:#1c2e48;--text:#e0e9f9;--muted:#9cacc6;--border:#2a3a54;--blue:#7799ff;--purple:#aa94ef;--green:#62bda4;--shadow:none}'
    theme = st.session_state.theme
    if theme == "Dark": content += dark
    if theme == "System": content += '@media(prefers-color-scheme:dark){' + dark + '}'
    if st.session_state.density == "Compact":
        content += '.kpi-card{padding:10px 13px;height:108px}.st-key-global_filters{padding:8px 14px}.stApp [data-testid="stVerticalBlock"]{gap:.7rem}.page-heading{padding:5px 0 8px}'
    if st.session_state.presentation:
        content += '[data-testid="stSidebar"],[data-testid="stExpandSidebarButton"]{display:none!important}[data-testid="stMainBlockContainer"]{max-width:1550px}.kpi-value{font-size:2.3rem}.kpi-card{height:145px}.kpi-label{font-size:.85rem}'
    st.html(f"<style>{content}</style>")


def render():
    started = perf_counter()
    sidebar()
    header()
    demo_notice()
    route = st.session_state.route
    if route not in PAGES:
        route = "overview"
        st.session_state.route = route
    title, description, view = PAGES[route]
    page_title(title, description)
    if route == "overview":
        hour = datetime.now().astimezone().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        st.markdown(f"### {greeting}. Here’s what changed.")
        st.caption("Review delivery and demand signals in the selected demo snapshot. Global filters below set the context for every analysis.")
    query_start = perf_counter()
    try:
        df = filters()
    except (RuntimeError, ConnectionError, ValueError) as error:
        service_error(error)
        return
    st.session_state.last_query_ms = round((perf_counter() - query_start) * 1000, 2)
    no_data_ok = {"profitability", "cross_risk", "settings", "diagnostics", "lineage", "drift", "health", "changes", "reports"}
    if df.empty and route not in no_data_ok:
        empty_state()
        evidence(df)
        return
    if st.session_state.copilot_open and route != "copilot" and st.session_state.copilot_enabled:
        main, drawer = st.columns([3.8, 1])
        with drawer:
            context_drawer()
            nav_button("Open Copilot workspace →", "copilot", key="drawer_open")
        with main:
            try:
                view(df)
            except Exception:
                page_error(route)
    else:
        with st.container(key="dashboard"):
            try:
                view(df)
            except Exception:
                page_error(route)
    if route not in {"settings", "diagnostics", "copilot", "changes"}:
        evidence(df)
    st.session_state.last_render_ms = round((perf_counter() - started) * 1000, 2)

