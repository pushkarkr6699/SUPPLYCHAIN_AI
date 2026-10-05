import streamlit as st
from components.tables import records_table
from components.section_header import section
from services.analytics import quality
from services.export_service import excel_bytes
from services.provider import get_service, filter_description


def render(df):
    service = get_service()
    dataset = st.selectbox("Dataset", ["delivery", "demand"], format_func=lambda name: ("Delivery orders" if name == "delivery" else "Demand forecast") + (" · demo" if service.demo else " · supplied data"), key="data_dataset")
    active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == dataset else st.session_state.get("filters_by_dataset", {}).get(dataset, {})
    df = service.records(active, dataset=dataset)
    source = df.attrs.get("data_source", "DEMO UI DATA")
    default = ["Order", "Date", "Market", "Region", "Risk Probability", "Risk"] if dataset == "delivery" else ["Date", "Product", "Category", "Actual Demand", "Forecast Demand", "Lower", "Upper"]
    column_query = st.text_input("Search column names", placeholder="e.g. product, probability, region")
    options = [column for column in df.columns if not column_query.strip() or column_query.casefold() in column.casefold()]
    chosen_default = [column for column in default if column in options]
    left, middle, right = st.columns([2, 1, 1])
    columns = left.multiselect("Columns", options, default=chosen_default, key=f"data_columns_{dataset}")
    sort = middle.selectbox("Sort by", df.columns, key=f"data_sort_{dataset}")
    descending = right.checkbox("Descending", value=True)
    value_query = st.text_input("Search values", placeholder="Search visible rows across the selected dataset")
    st.caption(f"{source} · " + filter_description(active, "All records in selected dataset"))
    if not columns:
        st.info("Select at least one column to display the data grid.")
        return
    view = df.copy()
    if value_query.strip():
        matches = view.astype(str).apply(lambda series: series.str.contains(value_query.strip(), case=False, regex=False)).any(axis=1)
        view = view[matches]
    view = view.sort_values(sort, ascending=not descending)[columns]
    section("Data grid", f"{len(view):,} rows · {len(columns)} selected columns · {source}")
    records_table(view, f"data_grid_{dataset}", investigate=False)
    prefix = "demo" if service.demo else "supplied"
    st.download_button("Download Excel", excel_bytes(view), f"{prefix}-{dataset}-filtered-data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("Advanced · schema, types, missing values and statistics"):
        st.dataframe(quality(view), hide_index=True, width="stretch")
        st.dataframe(view.describe(include="all").astype(str), width="stretch")

