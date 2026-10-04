from datetime import timedelta
import streamlit as st
from services.provider import get_service, FILTER_COLUMNS
from components.filter_chips import filter_chips
from components.navigation import go


PAGE_FILTERS = {
    "overview": ["Market", "Region", "Risk", "Category"],
    "delivery": ["Market", "Region", "Shipping Mode", "Risk"],
    "demand": ["Market", "Category", "Department", "Product"],
    "profitability": ["Market", "Region", "Category"],
    "cross_risk": ["Market", "Region", "Risk"],
    "orders": ["Market", "Region", "Risk", "Product"],
    "explorer": ["Market", "Region", "Risk", "Product"],
    "geography": ["Market", "Region", "Country", "Risk"],
    "changes": ["Market", "Region", "Category", "Risk"],
    "scenarios": ["Market", "Risk", "Product"],
    "insights": ["Market", "Region", "Risk", "Category"],
    "alerts": ["Market", "Region", "Risk"],
    "data": ["Market", "Region", "Risk", "Product"],
    "quality": ["Market", "Region", "Category"],
    "settings": [],
    "lineage": [],
    "diagnostics": [],
}


def reset_filters():
    st.session_state.filters = {}
    for key in list(st.session_state):
        if key.startswith("filter_"):
            del st.session_state[key]


def restore_view():
    name = st.session_state.get("saved_view_choice")
    saved = st.session_state.saved_views.get(name)
    if saved:
        reset_filters()
        st.session_state.filters = {key: value for key, value in saved.items() if key != "__meta__"}
        meta = saved.get("__meta__", {})
        if meta.get("dimension"):
            st.session_state.selected_dimension = meta["dimension"]
        if meta.get("metric"):
            st.session_state.selected_metric = meta["metric"]
        if meta.get("page"):
            go(meta["page"])


def rename_view():
    old = st.session_state.get("saved_view_choice")
    new = st.session_state.get("rename_view_name", "").strip()
    if old in st.session_state.saved_views and new and new != old:
        st.session_state.saved_views[new] = st.session_state.saved_views.pop(old)
        st.session_state.saved_view_choice = new


def delete_view():
    name = st.session_state.get("saved_view_choice")
    st.session_state.saved_views.pop(name, None)
    remaining = list(st.session_state.saved_views)
    if remaining:
        st.session_state.saved_view_choice = remaining[0]
    else:
        st.session_state.pop("saved_view_choice", None)
    st.session_state.pop("rename_view_name", None)


def filters():
    service = get_service()
    frame, options = service.records(), service.options()
    if frame.empty:
        return frame
    if st.session_state.route in {"settings", "lineage", "diagnostics"}:
        df = service.records(st.session_state.filters)
        st.caption(f"{len(df):,} Demo Records · workspace filter context preserved")
        return df
    with st.container(key="global_filters"):
        date_value = st.session_state.filters.get(
            "Date",
            (max(frame.Date.min().date(), frame.Date.max().date() - timedelta(days=st.session_state.default_days - 1)), frame.Date.max().date()),
        )
        visible = [name for name in PAGE_FILTERS.get(st.session_state.route, ["Market", "Region", "Risk"]) if name in FILTER_COLUMNS]
        spare = [name for name in FILTER_COLUMNS if name not in visible]
        widths = [1.45] + [1.15] * len(visible) + [1.0, .72]
        cols = st.columns(widths, vertical_alignment="bottom")
        with cols[0]:
            dates = st.date_input("Date", value=tuple(date_value), min_value=frame.Date.min().date(), max_value=frame.Date.max().date(), key="filter_Date", format="DD/MM/YYYY")
        st.session_state.filters["Date"] = dates
        for col, name in zip(cols[1:1 + len(visible)], visible):
            with col:
                value = st.multiselect(name, options[name], default=st.session_state.filters.get(name, []), placeholder="All", key=f"filter_{name}", label_visibility="visible")
                st.session_state.filters[name] = value
        with cols[-2]:
            with st.popover("Save view", icon=":material/bookmark:", width="stretch"):
                view_name = st.text_input("View name", key="view_name", max_chars=60)
                if st.button("Save current view", disabled=not bool(view_name.strip()), key="save_workspace_view"):
                    st.session_state.saved_views[view_name.strip()] = {
                        **st.session_state.filters,
                        "__meta__": {
                            "page": st.session_state.route,
                            "dimension": st.session_state.get("selected_dimension"),
                            "metric": st.session_state.get("selected_metric"),
                        },
                    }
                    st.success("View saved for this session.")
                if st.session_state.saved_views:
                    st.selectbox("Saved views", list(st.session_state.saved_views), key="saved_view_choice")
                    action_cols = st.columns(3)
                    action_cols[0].button("Open view", on_click=restore_view, key="restore_workspace_view", width="stretch")
                    action_cols[1].text_input("Rename", key="rename_view_name", label_visibility="collapsed", placeholder="New name")
                    action_cols[1].button("Rename", on_click=rename_view, key="rename_workspace_view", width="stretch")
                    action_cols[2].button("Delete", on_click=delete_view, key="delete_workspace_view", width="stretch")
        with cols[-1]:
            st.button("Reset", on_click=reset_filters, width="stretch", key="reset_workspace_filters")
        if spare:
            with st.expander("More filters", icon=":material/tune:"):
                extra_cols = st.columns(min(4, len(spare)))
                for i, name in enumerate(spare):
                    with extra_cols[i % len(extra_cols)]:
                        value = st.multiselect(name, options[name], default=st.session_state.filters.get(name, []), key=f"filter_{name}")
                        st.session_state.filters[name] = value
        filter_chips()
        df = service.records(st.session_state.filters)
        st.caption(f"{len(df):,} Demo Records in view · Filters apply across the workspace")
    return df
