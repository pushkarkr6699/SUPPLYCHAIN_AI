import pandas as pd
import plotly.express as px
import streamlit as st
from components.kpi_cards import kpis
from components.section_header import section
from components.charts import forecast_chart, bar, show
from components.tables import records_table
from components.status import badge
from services.analytics import summary, product_errors, aggregate
from config import DELIVERY_MODEL


def render(df):
    st.html(f'<div class="model-meta-row">{badge("Next-Day Forecast", "info")} {badge(DELIVERY_MODEL, "neutral")} {badge("Demo Data", "success")}<span>Forecast and validation fixtures · no live model execution</span></div>')
    m = summary(df)
    bias = float((df["Forecast Demand"] - df["Actual Demand"]).mean()) if len(df) else 0
    uncertainty = float((df["Upper"] - df["Lower"]).mean()) if len(df) else 0
    kpis([
        ("Actual Demand", m["actual"], "number", "Synthetic demand units"),
        ("Forecast Demand", m["forecast"], "number", "Demo forecast units", "purple"),
        ("WAPE", m["wape"], "percent", "Synthetic error metric", "amber"),
        ("SMAPE", m["smape"], "percent", "Synthetic error metric"),
        {"label": "Forecast Bias", "value": bias, "kind": "decimal", "caption": "Forecast minus actual · units", "tone": "purple"},
        {"label": "Mean Range Width", "value": uncertainty, "kind": "decimal", "caption": "Illustrative interval · units"},
    ])
    overview, seasonality, errors_tab, products = st.tabs(["Forecast Overview", "Seasonality", "Forecast Errors", "Product Explorer"])
    with overview:
        hero, health = st.columns([2, 1])
        with hero, st.container(border=True):
            section("Actual vs Forecast", "Forecast planning units · interval is illustrative, not calibrated")
            forecast_chart(df, "demand_main", 350)
        with health, st.container(border=True):
            section("Forecast Health", "Synthetic evaluation · not verified model performance")
            for label, value, detail in [("WAPE", m["wape"], "weighted absolute error"), ("SMAPE", m["smape"], "symmetric absolute error"), ("Bias", bias, "forecast − actual units"), ("Uncertainty", uncertainty, "mean range width")]:
                st.metric(label, f"{value:.1%}" if label in {"WAPE", "SMAPE"} else f"{value:,.1f}", help=detail)
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("High-Demand Products", "Forecast demand units by product")
            bar(df, "Product", "Forecast Demand", "demand_products", horizontal=True)
        with right, st.container(border=True):
            section("Demand by Category", "Forecast units in the selected context")
            bar(df, "Category", "Forecast Demand", "demand_category")
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Department Demand", "Forecast units by department")
            bar(df, "Department", "Forecast Demand", "demand_department")
        with right, st.container(border=True):
            section("Stock Attention", "Illustrative demand rule · inventory is not connected")
            attention = df[df["Stock Attention"]][["Date", "Product", "Category", "Department", "Actual Demand", "Forecast Demand", "Lower", "Upper"]]
            st.dataframe(attention, hide_index=True, width="stretch")
            st.caption(f"{len(attention):,} synthetic observations flagged by the demo rule")
    with seasonality:
        data = df.assign(Weekday=df.Date.dt.day_name(), Week=df.Date.dt.isocalendar().week.astype(int))
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Day-of-week Demand", "Mean actual demand per synthetic record")
            day = data.groupby("Weekday", as_index=False)["Actual Demand"].mean()
            show(px.bar(day, x="Weekday", y="Actual Demand", category_orders={"Weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}), "demand_weekday")
        with right, st.container(border=True):
            section("Weekly Demand Heatmap", "Illustrative actual demand by weekday and week")
            pivot = data.pivot_table(index="Weekday", columns="Week", values="Actual Demand", aggfunc="mean")
            show(px.imshow(pivot, color_continuous_scale="Purples", aspect="auto"), "demand_season")
    with errors_tab:
        errors = product_errors(df)
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Largest Underprediction", "Products where actual demand exceeded forecast")
            under = df.assign(Error=df["Actual Demand"] - df["Forecast Demand"]).groupby("Product", as_index=False).Error.sum().query("Error > 0").nlargest(8, "Error")
            show(px.bar(under, x="Error", y="Product", orientation="h"), "demand_underprediction")
        with right, st.container(border=True):
            section("Largest Overprediction", "Products where forecast exceeded actual demand")
            over = df.assign(Error=df["Forecast Demand"] - df["Actual Demand"]).groupby("Product", as_index=False).Error.sum().query("Error > 0").nlargest(8, "Error")
            show(px.bar(over, x="Error", y="Product", orientation="h"), "demand_overprediction")
        with st.container(border=True):
            section("Forecast Error by Product", "Aggregate absolute error · synthetic observations")
            show(px.bar(errors.head(12), x="Absolute Error", y="Product", orientation="h"), "demand_error_ranking")
        st.caption("Underprediction and overprediction indicate observed differences only; they do not identify causes.")
    with products:
        query = st.text_input("Search products", placeholder="Product name")
        options = sorted(product for product in df.Product.unique() if query.casefold() in product.casefold())
        if not options:
            st.info("No products match the current filters and search.")
            return
        previous = st.session_state.get("selected_product")
        product = st.selectbox("Product", options, index=options.index(previous) if previous in options else 0)
        st.session_state.selected_product = product
        subset = df[df.Product.eq(product)]
        profile = summary(subset)
        section(product, f'{subset.Category.iloc[0]} · {subset.Department.iloc[0]} · demo product profile')
        kpis([
            ("Forecast", profile["forecast"], "number", "Demand units", "purple"),
            ("Demand Level", "Attention" if profile["stock"] else "Typical", "number", "Illustrative rule"),
            ("Inventory Status", "Not connected", "number", "Inventory data unavailable"),
            ("Average Error", profile["error"], "decimal", "Mean absolute error"),
        ])
        with st.container(border=True):
            section("Product Forecast", "Actual demand, forecast and illustrative range")
            forecast_chart(subset, "product_forecast")
