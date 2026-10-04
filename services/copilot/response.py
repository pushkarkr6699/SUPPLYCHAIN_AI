from services.mock_data import COPILOT_COPY
from services.analytics import summary, aggregate
from services.copilot.tools import compare_periods, demand_growth, find_high_risk_orders, get_forecast, query_data, segment_risk


def build(intent, df, selected_order=None):
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
    chart = aggregate(df, "Market")
    chart_x, chart_y = "Market", "Risk Probability"
    if intent == "demand":
        chart, chart_x, chart_y = table, "Product", "Absolute Error"
    elif intent == "demand_growth":
        chart, chart_x, chart_y = table, "Product", "Change"
    elif intent in {"market_risk", "region_risk"}:
        chart, chart_x, chart_y = table, table.columns[0], "MeanRisk"
    elif intent == "compare":
        chart = table
    return {"intent": intent, "title": title, "narrative": COPILOT_COPY[intent], "table": table,
            "route": route, "summary": summary(df), "chart": chart, "chart_x": chart_x,
            "chart_y": chart_y, "records": len(df)}
