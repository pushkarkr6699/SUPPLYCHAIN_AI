from html import escape
import streamlit as st
from components.navigation import GROUPS, go
from services.auth_service import logout
from components.brand import MARK


def navigation_items(items):
    for route, label, icon in items:
        st.button(label, key=f"nav_{route}", icon=f":material/{icon}:", width="stretch",
                  type="primary" if st.session_state.route == route else "tertiary", on_click=go, args=(route,))


def sidebar():
    with st.sidebar, st.container(key="sidebar_shell"):
        st.html(f'<div class="brand"><span class="brand-mark">{MARK}</span><div>SUPPLYCHAIN <b>AI</b><small>Decision Intelligence Platform</small></div></div><div class="workspace-tag"><span class="workspace-dot"></span>Decision Intelligence Workspace</div>')
        for group, items in GROUPS.items():
            visible_items = [(route, label, icon) for route, label, icon in items if route != "diagnostics" or st.session_state.developer_mode]
            if not visible_items:
                continue
            if group == "COMMAND CENTER":
                st.html('<div class="nav-group">WORKSPACE</div>')
                navigation_items(visible_items)
            elif group == "INTELLIGENCE":
                navigation_items([item for item in visible_items if item[0] in {"delivery", "demand"}])
                other = [item for item in visible_items if item[0] not in {"delivery", "demand"}]
                with st.expander("Additional intelligence", expanded=st.session_state.route in {item[0] for item in other}):
                    navigation_items(other)
            elif group == "ANALYSIS":
                navigation_items([item for item in visible_items if item[0] in {"orders", "comparison"}])
                other = [item for item in visible_items if item[0] not in {"orders", "comparison"}]
                with st.expander("Explore & simulate", expanded=st.session_state.route in {item[0] for item in other}):
                    navigation_items(other)
            else:
                label = {"AI": "Copilot & insights", "ML GOVERNANCE": "Models & validation", "DATA": "Data & provenance", "OUTPUTS": "Reports & exports", "SYSTEM": "Settings & system"}[group]
                with st.expander(label, expanded=st.session_state.route in {item[0] for item in visible_items}):
                    navigation_items(visible_items)
        with st.container(key="sidebar_footer"):
            from services.provider import get_service
            demo = get_service().demo
            mode, state = ("DEMO UI MODE", "Demo state") if demo else ("VERIFIED DATA MODE", "CSV connected")
            st.html(f'<div class="sidebar-health"><div class="sidebar-status"><span class="status-dot"></span><b>System status</b><span>Operational</span></div><div class="sidebar-demo">{mode}</div><p>Delivery <span>{state}</span></p><p>Demand <span>{state}</span></p><p>Profitability <span>Not connected</span></p></div>')
            st.html(f'<div class="user-block"><span class="avatar">DA</span><div>{escape(st.session_state.user_name)}<small>Session-only workspace</small></div></div>')
            st.button("Log out", icon=":material/logout:", on_click=logout, width="stretch", key="sidebar_logout")
