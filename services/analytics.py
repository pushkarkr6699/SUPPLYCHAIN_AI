"""Pure calculations over supplied records, reusable by future real providers."""
import math
import numpy as np
import pandas as pd
from config import PRODUCTION_THRESHOLD
from services.mock_data import DEMO_AS_OF


def summary(df: pd.DataFrame) -> dict:
    n = len(df)
    if not n:
        return dict(orders=0, high=0, risk=None, forecast=None, actual=None, stock=0, alerts=0, predicted=0, late=0, accuracy=None, error=None, wape=None, smape=None, products=0)
    is_delivery = {"Risk Probability", "Risk", "Actual Late"}.issubset(df.columns)
    is_demand = {"Forecast Demand", "Actual Demand"}.issubset(df.columns)
    error = (df["Forecast Demand"] - df["Actual Demand"]).abs() if is_demand else None
    risk = float(df["Risk Probability"].mean()) if is_delivery else None
    late = int(df["Actual Late"].sum()) if is_delivery else None
    accuracy = (float(df["Correct Prediction"].mean()) if "Correct Prediction" in df else
                float(((df["Risk Probability"] >= PRODUCTION_THRESHOLD) == df["Actual Late"]).mean()) if is_delivery else None)
    actual_total = float(df["Actual Demand"].sum()) if is_demand else None
    forecast_total = float(df["Forecast Demand"].sum()) if is_demand else None
    wape = float(error.sum() / actual_total) if is_demand and actual_total else None
    smape = float((2 * error / (df["Forecast Demand"] + df["Actual Demand"]).replace(0, np.nan)).mean()) if is_demand else None
    stock = int(df["Stock Attention"].sum()) if "Stock Attention" in df else None
    high = int(df.Risk.isin(["High", "Critical"]).sum()) if "Risk" in df else None
    return {
        "orders": n, "high": high, "risk": risk,
        "forecast": forecast_total if is_demand else None,
        "actual": actual_total if is_demand else None, "stock": stock,
        "alerts": len(alerts(df)) if {"Risk", "Stock Attention", "Forecast Demand", "Actual Demand"}.issubset(df.columns) else 0,
        "predicted": int(df["Predicted Late"].sum()) if "Predicted Late" in df else int((df["Risk Probability"] >= PRODUCTION_THRESHOLD).sum()) if is_delivery else 0,
        "late": late, "accuracy": accuracy,
        "error": float(error.mean()) if is_demand else None, "wape": wape, "smape": smape,
        "products": df.loc[df["Stock Attention"], "Product"].nunique() if "Product" in df and "Stock Attention" in df else 0,
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

