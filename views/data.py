import streamlit as st
from components.tables import records_table
from components.section_header import section
from services.analytics import quality
from services.export_service import excel_bytes


def render(df):
    source = st.selectbox("Dataset", ["Delivery scored orders · demo", "Demand forecast · demo"])
    default = ["Order", "Date", "Market", "Region", "Risk Probability", "Risk"] if source.startswith("Delivery") else ["Date", "Product", "Category", "Actual Demand", "Forecast Demand", "Lower", "Upper"]
    column_query = st.text_input("Search column names", placeholder="e.g. product, probability, region")
    options = [column for column in df.columns if not column_query.strip() or column_query.casefold() in column.casefold()]
    chosen_default = [column for column in default if column in options]
    left, middle, right = st.columns([2, 1, 1])
    columns = left.multiselect("Columns", options, default=chosen_default, key=f"data_columns_{source}")
    sort = middle.selectbox("Sort by", df.columns)
    descending = right.checkbox("Descending", value=True)
    value_query = st.text_input("Search values", placeholder="Search visible rows across the selected dataset")
    st.caption("Use the global filter bar to filter this dataset. Only non-sensitive synthetic fields are available.")
    if not columns:
        st.info("Select at least one column to display the data grid.")
        return
    view = df.copy()
    if value_query.strip():
        matches = view.astype(str).apply(lambda series: series.str.contains(value_query.strip(), case=False, regex=False)).any(axis=1)
        view = view[matches]
    view = view.sort_values(sort, ascending=not descending)[columns]
    section("Data grid", f"{len(view):,} rows · {len(columns)} selected columns · DEMO UI DATA")
    records_table(view, "data_grid", investigate=False)
    st.download_button("Download Excel", excel_bytes(view), "demo-filtered-data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("Advanced · schema, types, missing values and statistics"):
        st.dataframe(quality(view), hide_index=True, width="stretch")
        st.dataframe(view.describe(include="all").astype(str), width="stretch")

