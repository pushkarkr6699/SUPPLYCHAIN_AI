import pandas as pd
from services.analytics import summary


def compare_periods(df, current, previous):
    current_df = df[df.Date.dt.date.between(current[0], current[1])]
    previous_df = df[df.Date.dt.date.between(previous[0], previous[1])]
    return current_df, previous_df


def change_table(current, previous):
    a, b = summary(current), summary(previous)
    metrics = [("Delivery risk", "risk", True), ("High-risk orders", "high", False), ("Demand units", "actual", False), ("Forecast error (MAE)", "error", False), ("Stock attention", "stock", False), ("Order volume", "orders", False)]
    rows = []
    for name, key, rate in metrics:
        if a[key] is None or b[key] is None:
            continue
        difference = a[key] - b[key]
        rows.append({"Metric": name, "Current": a[key], "Comparison": b[key], "Absolute change": difference,
            "Percentage change": difference / b[key] if b[key] else None,
            "Percentage-point change": difference * 100 if rate else None,
            "Direction": "Observed increase" if difference > 0 else "Observed decrease" if difference < 0 else "No observed change"})
    return pd.DataFrame(rows)

