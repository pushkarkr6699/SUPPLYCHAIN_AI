import streamlit as st
from components.navigation import go
from services.export_service import csv_bytes

ORDER_COLUMNS = ["Order", "Date", "Market", "Region", "Product", "Shipping Mode", "Risk Probability", "Risk"]


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
        view = view.sort_values("Risk Probability", ascending=False)

    preferred = [column for column in ORDER_COLUMNS if column in view] if investigate else list(view.columns)
    with toolbar[2].popover("Columns", icon=":material/view_column:"):
        columns = st.multiselect("Visible columns", list(view.columns), default=preferred, key=f"table_columns_{key}")
    toolbar[3].download_button("Download", csv_bytes(view), f"demo-{key}.csv", "text/csv", key=f"download_{key}", width="stretch")
    if not view.empty and not columns:
        st.info("Choose at least one column to display.")
        return
    if view.empty:
        st.info("No records match these table filters.")
        return

    limit = st.session_state.get("page_size", 15)
    maximum = max(1, (len(view) - 1) // limit + 1)
    page_key = f"page_{key}"
    if st.session_state.get(page_key, 1) > maximum:
        st.session_state[page_key] = maximum
    if maximum > 1:
        page = st.number_input("Page", min_value=1, max_value=maximum, value=st.session_state.get(page_key, 1), key=page_key, label_visibility="collapsed")
    else:
        page = 1
    display = view.iloc[(page - 1) * limit: page * limit]
    config = {
        "Risk Probability": st.column_config.ProgressColumn("Delivery risk", min_value=0, max_value=1, format="percent"),
        "Risk": st.column_config.TextColumn("Risk band", help="Relative demo risk band"),
    }
    st.dataframe(display[columns], hide_index=True, width="stretch", column_config=config)
    st.caption(f"Showing {(page - 1) * limit + 1:,}–{min(page * limit, len(view)):,} of {len(view):,} matching demo records")
    if investigate and "Order" in view:
        left, right = st.columns([3, 1])
        selected = left.selectbox("Investigate an order", view.Order.tolist(), key=f"investigate_{key}", label_visibility="collapsed")
        right.button("Open order", key=f"open_{key}", on_click=go, args=("orders",), kwargs={"selected_order": selected}, width="stretch")
