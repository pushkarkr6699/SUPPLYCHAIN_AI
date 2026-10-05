from services.mock_data import COPILOT_COPY
import pandas as pd
from services.analytics import summary, aggregate
from services.copilot.tools import compare_periods, demand_growth, find_high_risk_orders, get_forecast, query_data, segment_risk


def build(intent, df, selected_order=None):
    verified = bool(df.attrs.get("verified_artifacts"))
    required = {
        "demand": {"Product", "Actual Demand", "Forecast Demand"},
        "demand_growth": {"Date", "Product", "Actual Demand"},
        "market_risk": {"Order", "Market", "Risk", "Risk Probability"},
        "region_risk": {"Order", "Region", "Risk", "Risk Probability"},
        "compare": {"Market", "Risk Probability"},
        "change": {"Date"}, "explain": {"Order", "Risk", "Risk Probability"},
        "risk": {"Order", "Risk", "Risk Probability"},
    }
    unavailable = None
    if intent in required and not required[intent].issubset(df):
        target = "Demand" if intent in {"demand", "demand_growth"} else "Delivery"
        unavailable = f"This question needs {target.lower()} fields that are absent from the selected dataset. Select {target} in the Dataset control and ask again."
    elif intent in {"market_risk", "region_risk", "compare", "risk"} and not df["Risk Probability"].notna().any():
        unavailable = "There are no supplied delivery scores in the current filter context. Broaden the date range or remove segment filters to include scored orders."
    elif df.empty and intent != "unsupported":
        unavailable = "No rows match the current filters. Broaden the selected dataset's filters and ask again."
    if unavailable:
        intent = "unsupported"
    if intent == "demand":
        table, route, title = get_forecast(df), "demand", "Product forecast review"
    elif intent == "demand_growth":
        table, route, title = demand_growth(df), "demand", "Observed product demand change"
    elif intent in {"market_risk", "region_risk"}:
        dimension = "Region" if intent == "region_risk" else "Market"
        table, route, title = segment_risk(df, dimension), "geography", f"Delivery risk by {dimension.lower()}"
    elif intent == "compare":
        table = aggregate(df[df.Market.isin(["Europe", "LATAM"])], "Market")
        route, title = "geography", "Europe / LATAM comparison"
    elif intent == "change" and len(df):
        table, route, title = compare_periods(df), "changes", "Observed period changes"
    elif intent == "explain":
        selected = df[df.Order.eq(selected_order)] if selected_order else df.head(0)
        table = query_data(selected, ["Order", "Risk Probability", "Risk"])
        route, title = "explainability", "Explanation readiness"
    elif intent == "risk":
        table, route, title = find_high_risk_orders(df), "delivery", "Delivery signal review"
    else:
        table, route, title = query_data(df, ["Order", "Market"], limit=0), "overview", "Offline interface preview"
    chart = aggregate(df.dropna(subset=["Risk Probability"]), "Market") if {"Market", "Risk Probability"}.issubset(df) and intent != "unsupported" else pd.DataFrame()
    chart_x, chart_y = "Market", "Risk Probability"
    if intent == "demand":
        chart, chart_x, chart_y = table, "Product", "Absolute Error"
    elif intent == "demand_growth":
        chart, chart_x, chart_y = table, "Product", "Change"
    elif intent in {"market_risk", "region_risk"}:
        chart, chart_x, chart_y = table, table.columns[0], "MeanRisk"
    elif intent == "compare":
        chart = table
    if verified:
        narratives = {
            "demand": "Product errors are calculated from supplied next-day actual visits and forecasts. This describes the supplied observations, not future accuracy.",
            "demand_growth": "Demand change compares mean daily actual visits in the earlier and later halves of the selected period. Products require observations in both halves.",
            "market_risk": "Markets are ranked by mean supplied probability among scored orders. Total and scored-order counts show coverage; unscored orders are excluded from risk averages.",
            "region_risk": "Regions are ranked by mean supplied probability among scored orders. Total and scored-order counts show coverage; unscored orders are excluded from risk averages.",
            "compare": "This compares mean supplied delivery probability for Europe and LATAM in the current filters. Different score coverage may affect the comparison.",
            "change": "The earlier and later halves of the selected period are compared using available fields. These observed differences do not establish causal effects.",
            "explain": "The selected order's supplied score is shown when available. A score and global feature ranking do not establish a local causal explanation; per-order attribution is not supplied.",
            "risk": "These are the highest supplied delivery probabilities in the current context. Unscored orders are excluded and are not classified as low risk.",
            "unsupported": "Ask about delivery risk, market or region comparisons, forecast errors, product demand change, or period changes in the selected dataset. Live AI generation and unsupported model simulations are unavailable.",
        }
        narrative = unavailable or narratives[intent]
        if intent == "change" and "Risk Probability" not in df:
            route = "demand"
    else:
        narrative = unavailable or COPILOT_COPY[intent]
    table.attrs.update(df.attrs)
    chart.attrs.update(df.attrs)
    return {"intent": intent, "title": title, "narrative": narrative, "table": table,
            "route": route, "summary": summary(df), "chart": chart, "chart_x": chart_x,
            "chart_y": chart_y, "records": len(df)}
