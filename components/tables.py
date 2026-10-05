import streamlit as st
from components.navigation import go
from services.export_service import csv_bytes
from components.feedback import download_feedback

ORDER_COLUMNS = ["Order", "Date", "Market", "Region", "Product", "Shipping Mode", "Risk Probability", "Risk"]


def change_table_page(page_key, direction, maximum):
    current = st.session_state.get(page_key, 1)
    st.session_state[page_key] = min(maximum, max(1, current + direction))


def records_table(df, key="records", search=True, investigate=True):
    if df.empty:
        st.info("No records match the current filters.")
        return
    view = df.copy()
    toolbar = st.columns([2.2, 1, 1, 1])
    if search:
        query = toolbar[0].text_input("Search records", placeholder="Search order, market, product…", key=f"table_search_{key}", label_visibility="collapsed")
        if query:
            view = view[view.astype(str).apply(lambda series: series.str.contains(query, case=False, regex=False)).any(axis=1)]
    else:
        toolbar[0].caption(f"{len(view):,} records")

    if investigate:
        with toolbar[1].popover("Filters", icon=":material/filter_list:"):
            for column in ["Risk", "Market", "Region"]:
                if column in view:
                    options = sorted(df[column].dropna().unique().tolist())
                    selected_values = st.multiselect(column, options, key=f"table_filter_{key}_{column}")
                    if selected_values:
                        view = view[view[column].isin(selected_values)]
    if investigate and not view.empty and "Risk Probability" in view:
        view = view.sort_values("Risk Probability", ascending=False, na_position="last", kind="stable")
        toolbar[0].caption("Default order: highest delivery risk first · click a column heading to sort the displayed page.")

    preferred = [column for column in ORDER_COLUMNS if column in view] if investigate else list(view.columns)
    with toolbar[2].popover("Columns", icon=":material/view_column:"):
        column_key = f"table_columns_{key}"
        if column_key in st.session_state:
            valid = [c for c in st.session_state[column_key] if c in view]
            if valid != st.session_state[column_key]:
                st.session_state[column_key] = valid
        columns = st.multiselect("Visible columns", list(view.columns), default=None if column_key in st.session_state else preferred, key=column_key)
    prefix = "verified" if df.attrs.get("verified_artifacts") else "demo"
    toolbar[3].download_button("Download", csv_bytes(view), f"{prefix}-{key}.csv", "text/csv", key=f"download_{key}", width="stretch", on_click=download_feedback, args=("CSV download",))
    if not view.empty and not columns:
        st.info("Choose at least one column to display.")
        return
    if view.empty:
        st.info("No records match these table filters.")
        return

    limit = max(1, st.session_state.get("page_size", 15))
    maximum = max(1, (len(view) - 1) // limit + 1)
    page_key = f"page_{key}"
    page = min(maximum, max(1, st.session_state.get(page_key, 1)))
    if st.session_state.get(page_key) != page:
        st.session_state[page_key] = page
    display = view.iloc[(page - 1) * limit: page * limit]
    config = {
        "Order": st.column_config.TextColumn("Order ID", pinned=True, help="Pinned identifier for this order"),
        "Date": st.column_config.DatetimeColumn("Order date", format="DD MMM YYYY"),
        "Risk Probability": st.column_config.ProgressColumn("Delivery risk", min_value=0, max_value=1, format="percent"),
        "Risk": st.column_config.TextColumn("Risk band", help="Supplied risk band; blank means unscored" if df.attrs.get("verified_artifacts") else "Relative demo risk band"),
    }
    st.dataframe(display[columns], hide_index=True, width="stretch", column_config=config, row_height=40)
    with st.container(key=f"table_footer_{key}"):
        count, controls = st.columns([1.7, 2.3], vertical_alignment="center", gap="small")
        count.caption(f"Showing {(page - 1) * limit + 1:,}–{min(page * limit, len(view)):,} of {len(view):,} matching {prefix} records")
        with controls:
            with st.container(key=f"table_pagination_{key}"):
                previous, position, following, jump = st.columns([1.1, 1.2, .85, .85], vertical_alignment="center", gap="small")
                previous.button("Previous", disabled=page == 1, key=f"previous_page_{key}", on_click=change_table_page, args=(page_key, -1, maximum), width="stretch")
                position.markdown(f'<p class="table-page-status" role="status" aria-live="polite">Page {page:,} of {maximum:,}</p>', unsafe_allow_html=True)
                following.button("Next", disabled=page == maximum, key=f"next_page_{key}", on_click=change_table_page, args=(page_key, 1, maximum), width="stretch")
                if maximum > 1:
                    with jump.popover("Jump", icon=":material/more_horiz:", width="stretch"):
                        with st.container(key=f"table_page_jump_{key}"):
                            st.number_input("Page", min_value=1, max_value=maximum, step=1, key=page_key)
    if investigate and "Order" in view:
        with st.container(key=f"table_investigation_{key}"):
            st.markdown('<h3 class="table-investigation-title">Order investigation</h3><p class="table-investigation-copy">Choose an order from the matching records to inspect its evidence.</p>', unsafe_allow_html=True)
            left, right = st.columns([3, 1], vertical_alignment="bottom")
            selected = left.selectbox("Investigate an order", view.Order.tolist(), key=f"investigate_{key}", label_visibility="collapsed")
            right.button("Open order", key=f"open_{key}", on_click=go, args=("orders",), kwargs={"selected_order": selected}, width="stretch")
