from components.secure_actions import download_button
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
    demo = not df.attrs.get("verified_artifacts", False)
    if not demo:
        st.caption("Demand represents web visits. Dates below are base dates; each prediction targets the following day. Inventory and purchased units are not supplied.")
    st.html(f'<div class="model-meta-row">{badge("Next-Day Forecast", "info")} {badge(DELIVERY_MODEL if demo else "Supplied forecast CSV", "neutral")} {badge("Demo Data" if demo else "Forecast Output Connected", "success")}<span>{"Synthetic fixtures · no live model execution" if demo else df.attrs.get("artifact", "supplied forecast output") + " · trained model controls below"}</span></div>')
    m = summary(df)
    bias = float((df["Forecast Demand"] - df["Actual Demand"]).mean()) if len(df) else 0
    uncertainty = float((df["Upper"] - df["Lower"]).mean()) if len(df) else 0
    interval_coverage = float(df["Actual Demand"].between(df["Lower"], df["Upper"]).mean()) if len(df) else 0
    kpis([
        ("Actual Demand", m["actual"], "number", "Synthetic demand units" if demo else "Supplied next-day actual web visits"),
        ("Forecast Demand", m["forecast"], "number", "Demo forecast units" if demo else "Supplied next-day forecast web visits", "purple"),
        ("WAPE", m["wape"], "percent", "Synthetic error metric" if demo else "Descriptive error on supplied scored rows", "amber"),
        ("SMAPE", m["smape"], "percent", "Synthetic error metric" if demo else "Descriptive error on supplied scored rows"),
        {"label": "Forecast Bias", "value": bias, "kind": "decimal", "caption": "Forecast minus actual · units", "tone": "purple"},
        {"label": "Mean Range Width", "value": uncertainty, "kind": "decimal", "caption": "Illustrative interval · units" if demo else "Source bounds labeled 90% · calibration unverified"},
    ])
    overview, seasonality, errors_tab, products = st.tabs(["Forecast Overview", "Seasonality", "Forecast Errors", "Product Explorer"])
    with overview:
        hero, health = st.columns([2, 1])
        with hero, st.container(border=True):
            interval_note = (f'Source bounds are named 90%; observed in-row coverage in this context is {interval_coverage:.1%}. Calibration provenance is unavailable.' if not demo else "Forecast planning units · interval is illustrative, not calibrated")
            section("Actual vs Forecast", interval_note)
            forecast_chart(df, "demand_main", 350)
        with health, st.container(border=True):
            section("Forecast Health", "Synthetic evaluation · not verified model performance" if demo else "Descriptive errors on supplied scored forecast rows; evaluation split provenance unavailable")
            for label, value, detail in [("WAPE", m["wape"], "weighted absolute error"), ("SMAPE", m["smape"], "symmetric absolute error"), ("Bias", bias, "forecast − actual units"), ("Uncertainty", uncertainty, "mean range width"), ("Interval coverage", interval_coverage, "observed source-row coverage")]:
                display = "N/A" if value is None else f"{value:.1%}" if label in {"WAPE", "SMAPE", "Interval coverage"} else f"{value:,.1f}"
                st.metric(label, display, help=detail)
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
            section("Stock Attention", "Illustrative demand rule · inventory is not connected" if demo else "Supplied stock-attention flag from the forecast output")
            attention = df[df["Stock Attention"]][["Date", "Product", "Category", "Department", "Actual Demand", "Forecast Demand", "Lower", "Upper"]]
            st.dataframe(attention, hide_index=True, width="stretch")
            st.caption(f'{len(attention):,} {"synthetic observations flagged by the demo rule" if demo else "supplied forecast rows flagged for stock review"}')
    with seasonality:
        data = df.assign(Weekday=df.Date.dt.day_name(), Week=df.Date.dt.isocalendar().week.astype(int))
        left, right = st.columns(2)
        with left, st.container(border=True):
            section("Day-of-week Demand", "Mean actual demand per synthetic record" if demo else "Mean supplied next-day actual by forecast date weekday")
            day = data.groupby("Weekday", as_index=False)["Actual Demand"].mean()
            show(px.bar(day, x="Weekday", y="Actual Demand", category_orders={"Weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}), "demand_weekday")
        with right, st.container(border=True):
            section("Weekly Demand Heatmap", "Illustrative actual demand by weekday and week" if demo else "Supplied actual demand by weekday and week number")
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
            section("Forecast Error by Product", "Aggregate absolute error · synthetic observations" if demo else "Aggregate error from supplied product/day rows")
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
        section(product, f'{subset.Category.iloc[0]} · {subset.Department.iloc[0]} · {"demo product profile" if demo else "supplied product/day forecast profile"}')
        kpis([
            ("Forecast", profile["forecast"], "number", "Demand units", "purple"),
            ("Demand Level", str(subset["Demand Level"].iloc[-1]) if "Demand Level" in subset else "Attention" if profile["stock"] else "Typical", "number", "Source label" if not demo else "Illustrative rule"),
            ("Inventory Status", "Not connected", "number", "Inventory data unavailable"),
            ("Average Error", profile["error"], "decimal", "Mean absolute error"),
        ])
        with st.container(border=True):
            section("Product Forecast", "Actual demand, forecast and illustrative range" if demo else "Precomputed forecast with source-provided interval bounds")
            forecast_chart(subset, "product_forecast")
    if not demo:
        _prediction_lab()


def _prediction_lab():
    from services.access_control import can
    if not can('predict'):st.info('Model execution requires an Analyst or Admin account.');return
    from services.demand_inference import status, registered, SOURCE, predict_next_day
    availability = status()
    with st.expander("Run trained next-day web-visit forecast"):
        st.caption("Uses at least 15 consecutive days of observed visits per product. The supplied history ends 30 January 2018; predictions from it are historical estimates.")
        if not availability["available"]:
            st.warning(availability["reason"])
            return
        history = pd.read_csv(registered(SOURCE)[0])
        uploaded = st.file_uploader("Optional daily visits history CSV", type=["csv"], key="demand_history_upload",max_upload_size=20, help="Columns: DateOnly, Product, Category, Department, Visits. Include zero-visit days and at least 15 consecutive days per product.")
        if uploaded is not None:
            try:
                from services import upload_service as uploads
                history=uploads.parse(uploaded.getvalue(),uploaded.name)
                if len(history)>uploads.MAX_PREDICTION_ROWS:raise ValueError('Upload prediction batch limit exceeded.')
            except Exception:
                st.error('Cannot read visits history. Check the format, required columns and 5,000-row upload prediction limit.')
                return
        if st.button("Run trained demand model", key="run_demand_model"):
            try:
                result = predict_next_day(history)
                st.dataframe(result, hide_index=True, width="stretch")
                from services.export_service import csv_bytes
                download_button("Download trained forecasts", csv_bytes(result), "trained_web_visit_forecasts.csv", "text/csv", container=st)
                st.caption(f"{len(result):,} products · original trained XGBoost model · point forecasts in web visits. Prediction intervals are not generated for new history.")
            except Exception:
                st.error('Forecast inputs could not be validated. Check complete, nonnegative daily visits and at least 15 consecutive days per product.')
