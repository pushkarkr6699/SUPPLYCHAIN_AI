from copy import deepcopy
from datetime import timedelta
import streamlit as st
from services.provider import get_service
from components.filter_chips import filter_chips
from components.navigation import go


PAGE_FILTERS = {
    "overview": ["Market", "Region", "Risk", "Category"],
    "delivery": ["Market", "Region", "Shipping Mode", "Risk"],
    "models": ["Market", "Region", "Risk"],
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

ROUTE_DATASET = {
    "delivery": "delivery", "orders": "delivery", "geography": "delivery",
    "changes": "delivery", "threshold": "delivery", "explainability": "delivery", "models": "delivery",
    "demand": "demand",
}


def dataset_for_route(route):
    if get_service().demo:
        return "demo"
    if route in {"data", "quality", "downloads", "explorer", "comparison"}:
        return st.session_state.get(f"{route}_dataset", "delivery")
    if route == "copilot":
        return st.session_state.get("copilot_dataset", "delivery")
    return ROUTE_DATASET.get(route, "delivery")


def reset_filters():
    st.session_state.filters = {}
    # Recreate the date widget so its visible segments match the reset bounds.
    st.session_state.date_reset_revision = st.session_state.get("date_reset_revision", 0) + 1
    # Hidden popover widgets need a fresh identity to discard cached client values.
    st.session_state.filters_widget_revision = st.session_state.get("filters_widget_revision", 0) + 1
    dataset = st.session_state.get("active_filter_dataset", "demo")
    st.session_state.setdefault("filters_by_dataset", {})[dataset] = {}
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
            target_dataset = meta.get("dataset", dataset_for_route(meta["page"]))
            st.session_state.active_filter_dataset = target_dataset
            st.session_state.setdefault("filters_by_dataset", {})[target_dataset] = deepcopy({key: value for key, value in saved.items() if key != "__meta__"})
            go(meta["page"])
        st.toast("Saved view restored for this session.")


def rename_view():
    old = st.session_state.get("saved_view_choice")
    new = st.session_state.get("rename_view_name", "").strip()
    if old in st.session_state.saved_views and new and new != old:
        st.session_state.saved_views[new] = st.session_state.saved_views.pop(old)
        st.session_state.saved_view_choice = new
        st.toast("Saved view renamed.")


def delete_view():
    name = st.session_state.get("saved_view_choice")
    st.session_state.saved_views.pop(name, None)
    st.toast("Saved view deleted.")
    remaining = list(st.session_state.saved_views)
    if remaining:
        st.session_state.saved_view_choice = remaining[0]
    else:
        st.session_state.pop("saved_view_choice", None)
    st.session_state.pop("rename_view_name", None)


def filters():
    if st.session_state.route == "comparison":
        st.selectbox("Comparison dataset", ["delivery", "demand"], format_func=lambda name: "Delivery orders" if name == "delivery" else "Demand forecasts", key="comparison_dataset")
    service = get_service()
    dataset = dataset_for_route(st.session_state.route)
    st.session_state.setdefault("filters_by_dataset", {})
    previous_dataset = st.session_state.get("active_filter_dataset")
    if previous_dataset is None:
        st.session_state.active_filter_dataset = dataset
        st.session_state.filters_by_dataset[dataset] = deepcopy(st.session_state.filters)
    elif previous_dataset != dataset:
        st.session_state.filters_by_dataset[previous_dataset] = deepcopy(st.session_state.filters)
        st.session_state.filters = deepcopy(st.session_state.filters_by_dataset.get(dataset, {}))
        st.session_state.active_filter_dataset = dataset
    widget_scope = "" if dataset == "demo" else f"_{dataset}"
    frame, options = service.records(dataset=dataset), service.options(dataset=dataset)
    if frame.empty:
        return frame
    if st.session_state.route in {"settings", "lineage", "diagnostics"}:
        df = service.records(st.session_state.filters, dataset=dataset)
        st.caption(f"{len(df):,} records · {service.data_source_label(dataset)} · workspace filter context preserved")
        return df
    with st.container(key="global_filters"):
        date_min, date_max = frame.Date.min().date(), frame.Date.max().date()
        date_value = st.session_state.filters.get("Date")
        if not date_value or len(date_value) != 2 or date_value[1] < date_min or date_value[0] > date_max:
            date_value = (max(date_min, date_max - timedelta(days=st.session_state.default_days - 1)), date_max)
        else:
            date_value = (max(date_min, date_value[0]), min(date_max, date_value[1]))
        available_fields = [name for name in PAGE_FILTERS.get(st.session_state.route, list(options)) if name in options]
        essential = ["Market", "Risk"] if "Risk" in available_fields else ["Category", "Product"]
        visible = [name for name in essential if name in available_fields] or available_fields[:2]
        spare = [name for name in options if name not in visible]
        unapplied = [name for name, values in st.session_state.filters.items() if name != "Date" and values and name not in options]
        if unapplied:
            st.caption(f"Preserved but not applied to this dataset: {', '.join(unapplied)}")
        widths = [1.45] + [1.15] * len(visible) + [1.0, .72]
        cols = st.columns(widths, vertical_alignment="bottom")
        date_key = f"filter_Date{widget_scope}"
        revision = st.session_state.get("date_reset_revision", 0)
        if revision:
            date_key += f"_{revision}"
        stale_widget_date = st.session_state.get(date_key)
        if stale_widget_date and len(stale_widget_date) == 2 and (stale_widget_date[1] < date_min or stale_widget_date[0] > date_max):
            st.session_state.pop(date_key, None)
        with cols[0]:
            with st.container(key=f"date_control{widget_scope}_{revision}"):
                dates = st.date_input("Date", value=tuple(date_value), min_value=frame.Date.min().date(), max_value=frame.Date.max().date(), key=date_key, format="DD/MM/YYYY")
        st.session_state.filters["Date"] = dates
        for col, name in zip(cols[1:1 + len(visible)], visible):
            with col:
                widget_key = f"filter_{name}{widget_scope}"
                selected_values = st.session_state.filters.get(name, [])
                if any(value not in options[name] for value in selected_values):
                    st.session_state.pop(widget_key, None)
                    selected_values = [value for value in selected_values if value in options[name]]
                value = st.multiselect(name, options[name], default=selected_values, placeholder="All", key=widget_key, label_visibility="visible")
                st.session_state.filters[name] = value
        with cols[-2]:
            with st.popover("Save view", icon=":material/bookmark:", width="stretch"):
                view_name = st.text_input("View name", key="view_name", max_chars=60)
                if st.button("Save current view", disabled=not bool(view_name.strip()), key="save_workspace_view"):
                    st.session_state.saved_views[view_name.strip()] = {
                        **deepcopy(st.session_state.filters),
                        "__meta__": {
                            "page": st.session_state.route,
                            "dataset": dataset,
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
        with st.container(key="filter_secondary_row"):
            secondary = st.columns([1, 3.1, 1.9], vertical_alignment="center", gap="small") if spare else st.columns([3.1, 1.9], vertical_alignment="center", gap="small")
            if spare:
                with secondary[0]:
                    with st.container(key="filter_more_control"):
                        with st.popover("More filters", icon=":material/tune:", width="content"):
                            with st.container(key="advanced_filter_controls"):
                                extra_cols = st.columns(min(2, len(spare)))
                                for i, name in enumerate(spare):
                                    with extra_cols[i % len(extra_cols)]:
                                        widget_key = f"filter_{name}{widget_scope}"
                                        advanced_revision = st.session_state.get("filters_widget_revision", 0)
                                        if advanced_revision:
                                            widget_key += f"_{advanced_revision}"
                                        selected_values = st.session_state.filters.get(name, [])
                                        if any(value not in options[name] for value in selected_values):
                                            st.session_state.pop(widget_key, None)
                                            selected_values = [value for value in selected_values if value in options[name]]
                                        value = st.multiselect(name, options[name], default=selected_values, key=widget_key)
                                        st.session_state.filters[name] = value
            with secondary[-2]:
                with st.container(key="filter_active_summary"):
                    filter_chips(exclude=("Date", *visible) if st.session_state.route == "delivery" else ())
            df = service.records(st.session_state.filters, dataset=dataset)
            st.session_state.filters_by_dataset[dataset] = deepcopy(st.session_state.filters)
            with secondary[-1]:
                with st.container(key="filter_record_summary"):
                    st.caption(f"{len(df):,} {dataset} records in view")
    return df
