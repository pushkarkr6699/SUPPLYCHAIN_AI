from html import escape
import streamlit as st
from components.navigation import GROUPS, go
from services.auth_service import logout


def sidebar():
    with st.sidebar, st.container(key="sidebar_shell"):
        st.html('<div class="brand"><span class="brand-mark">S</span><div>SUPPLYCHAIN <b>AI</b><small>Decision Intelligence Platform</small></div></div><div class="workspace-tag"><span class="workspace-dot"></span>Decision Intelligence Workspace</div>')
        for group, items in GROUPS.items():
            visible_items = [(route, label, icon) for route, label, icon in items if route != "diagnostics" or st.session_state.developer_mode]
            if not visible_items:
                continue
            st.html(f'<div class="nav-group">{escape(group)}</div>')
            for route, label, icon in visible_items:
                st.button(label, key=f"nav_{route}", icon=f":material/{icon}:", width="stretch",
                    type="primary" if st.session_state.route == route else "tertiary", on_click=go, args=(route,))
        with st.container(key="sidebar_footer"):
            from services.provider import get_service
            demo = get_service().demo
            mode, state = ("DEMO UI MODE", "Demo state") if demo else ("VERIFIED DATA MODE", "CSV connected")
            st.html(f'<div class="sidebar-health"><div class="sidebar-status"><span class="status-dot"></span><b>System status</b><span>Operational</span></div><div class="sidebar-demo">{mode}</div><p>Delivery <span>{state}</span></p><p>Demand <span>{state}</span></p><p>Profitability <span>Not connected</span></p></div>')
            st.html(f'<div class="user-block"><span class="avatar">DA</span><div>{escape(st.session_state.user_name)}<small>Session-only workspace</small></div></div>')
            st.button("Log out", icon=":material/logout:", on_click=logout, width="stretch", key="sidebar_logout")
