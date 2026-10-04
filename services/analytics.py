"""Pure calculations over supplied records, reusable by future real providers."""
import math
import numpy as np
import pandas as pd
from config import PRODUCTION_THRESHOLD
from services.mock_data import DEMO_AS_OF


def summary(df: pd.DataFrame) -> dict:
    n = len(df)
    if not n:
        return dict(orders=0, high=0, risk=0, forecast=0, actual=0, stock=0, alerts=0, predicted=0, late=0, accuracy=0, error=0, wape=0, smape=0, products=0)
    error = (df["Forecast Demand"] - df["Actual Demand"]).abs()
    return {
        "orders": n, "high": int(df.Risk.isin(["High", "Critical"]).sum()),
        "risk": df["Risk Probability"].mean(), "forecast": int(df["Forecast Demand"].sum()),
        "actual": int(df["Actual Demand"].sum()), "stock": int(df["Stock Attention"].sum()),
        "alerts": len(alerts(df)), "predicted": int((df["Risk Probability"] >= PRODUCTION_THRESHOLD).sum()),
        "late": int(df["Actual Late"].sum()),
        "accuracy": ((df["Risk Probability"] >= PRODUCTION_THRESHOLD) == df["Actual Late"]).mean(),
        "error": float(error.mean()), "wape": float(error.sum() / df["Actual Demand"].sum()),
        "smape": float((2 * error / (df["Forecast Demand"] + df["Actual Demand"])).mean()),
        "products": df.loc[df["Stock Attention"], "Product"].nunique(),
    }


def aggregate(df, dimension, metric="Risk Probability"):
    operation = "mean" if metric == "Risk Probability" else "sum"
    if metric == "Orders":
        return df.groupby(dimension, observed=True).size().reset_index(name="Orders")
    if metric == "High-Risk Orders":
        return df.assign(**{metric: df.Risk.isin(["High", "Critical"]).astype(int)}).groupby(dimension, observed=True)[metric].sum().reset_index()
    return df.groupby(dimension, observed=True)[metric].agg(operation).reset_index()


def trend(df):
    return df.groupby("Date", as_index=False)[["Actual Demand", "Forecast Demand", "Lower", "Upper"]].sum()


def product_errors(df):
    grouped = df.assign(**{"Absolute Error": (df["Forecast Demand"] - df["Actual Demand"]).abs()}).groupby("Product", as_index=False)[["Actual Demand", "Forecast Demand", "Absolute Error"]].sum()
    grouped["WAPE"] = grouped["Absolute Error"] / grouped["Actual Demand"].clip(lower=1)
    return grouped.sort_values("Absolute Error", ascending=False)


def classification(df, threshold):
    p, y = df["Risk Probability"] >= threshold, df["Actual Late"]
    tp, tn, fp, fn = int((p & y).sum()), int((~p & ~y).sum()), int((p & ~y).sum()), int((~p & y).sum())
    precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return {"Precision": precision, "Recall": recall, "F1": 2 * precision * recall / max(precision + recall, 1e-9),
            "MCC": (tp * tn - fp * fn) / denominator if denominator else 0,
            "FPR": fp / max(fp + tn, 1), "TP": tp, "TN": tn, "FP": fp, "FN": fn}


def threshold_curve(df):
    return pd.DataFrame([{"Threshold": t, **classification(df, t)} for t in np.linspace(0, 1, 51)])


def quality(df):
    return pd.DataFrame({"Column": df.columns, "Type": [str(x) for x in df.dtypes],
        "Missing": df.isna().sum().values, "Unique": df.nunique().values})


def alerts(df):
    items = [
        {"Severity": "Critical", "Category": "Risk", "Title": "High delivery risk", "Description": "Review synthetic orders in the high and critical risk bands.", "Records": int(df.Risk.isin(["High", "Critical"]).sum()), "Route": "delivery"},
        {"Severity": "Attention", "Category": "Demand", "Title": "Inventory attention", "Description": "Illustrative forecast exceeds actual demand by more than 15%; inventory is not connected.", "Records": int(df["Stock Attention"].sum()), "Route": "demand"},
        {"Severity": "Attention", "Category": "Anomaly", "Title": "Forecast error review", "Description": "Investigate the largest absolute errors in the demo forecast.", "Records": len(df), "Route": "demand"},
        {"Severity": "Information", "Category": "Model", "Title": "Profitability model unavailable", "Description": "Profitability and combined risk remain disabled until verified artifacts are connected.", "Records": 0, "Route": "profitability"},
        {"Severity": "Information", "Category": "Data", "Title": "Synthetic data is active", "Description": "No operational dataset is loaded. Quality metrics describe demo fixtures only.", "Records": len(df), "Route": "quality"},
        {"Severity": "Information", "Category": "Concentration", "Title": "Market concentration", "Description": "Compare order volumes and risk across markets in the current filter context.", "Records": len(df), "Route": "geography"},
        {"Severity": "Information", "Category": "Trend", "Title": "Period comparison available", "Description": "Explore observed changes between two selected demo periods.", "Records": len(df), "Route": "changes"},
    ]
    for item in items:
        item["Timestamp"] = DEMO_AS_OF
        item["Source"] = "DEMO UI RULE"
        item["Evidence"] = f'{item["Records"]:,} synthetic records in the active context'
    return items

