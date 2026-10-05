"""Read-only analytical functions. No SQL, Python, or user code is evaluated."""
import pandas as pd
from services.analytics import aggregate, product_errors
from services.comparison_service import change_table


def query_data(df, columns, limit=100):
    safe = [name for name in columns if name in df.columns]
    return df.loc[:, safe].head(max(0, min(int(limit), 500))).copy()


def find_high_risk_orders(df, limit=8):
    columns = [name for name in ("Order", "Market", "Region", "Risk Probability", "Risk") if name in df]
    return df.dropna(subset=["Risk Probability"]).nlargest(max(0, min(int(limit), 100)), "Risk Probability")[columns].copy()


def calculate_metric(df, metric):
    if metric == "mean_delivery_risk":
        return float(df["Risk Probability"].mean()) if len(df) else None
    if metric == "forecast_demand":
        return float(df["Forecast Demand"].sum()) if len(df) else 0.0
    if metric == "forecast_wape":
        actual = float(df["Actual Demand"].sum()) if len(df) else 0.0
        return float((df["Forecast Demand"] - df["Actual Demand"]).abs().sum() / actual) if actual else None
    raise ValueError("Unsupported metric")


def compare_periods(df):
    if not len(df):
        return df.head(0)
    middle = df.Date.min() + (df.Date.max() - df.Date.min()) / 2
    return change_table(df[df.Date > middle], df[df.Date <= middle])


def get_forecast(df):
    return product_errors(df)


def demand_growth(df):
    if df.empty:
        return df.head(0)
    midpoint = df.Date.min() + (df.Date.max() - df.Date.min()) / 2
    current = df[df.Date > midpoint].groupby("Product")["Actual Demand"].mean().rename("Recent Average")
    previous = df[df.Date <= midpoint].groupby("Product")["Actual Demand"].mean().rename("Prior Average")
    result = pd.concat([previous, current], axis=1).dropna().reset_index()
    result["Change"] = result["Recent Average"] - result["Prior Average"]
    result["Change %"] = result["Change"] / result["Prior Average"].replace(0, float("nan"))
    result["Direction"] = result["Change"].map(lambda value: "Increasing" if value > 0 else "Decreasing" if value < 0 else "Flat")
    return result.sort_values("Change", ascending=False)


def segment_risk(df, dimension):
    if dimension not in {"Market", "Region"}:
        raise ValueError("Unsupported risk segment")
    return (df.assign(_high=df.Risk.isin(["High", "Critical"]).astype(int))
            .groupby(dimension, observed=True)
            .agg(Orders=("Order", "size"), ScoredOrders=("Risk Probability", "count"), MeanRisk=("Risk Probability", "mean"), HighRiskOrders=("_high", "sum"))
            .sort_values("MeanRisk", ascending=False).reset_index())


def get_model_metrics():
    from services.provider import get_service
    service = get_service()
    if service.demo:
        return {"available": False, "reason": "Verified model metrics are not connected in demo mode."}
    return {"available": True, "data": service.model_comparison().to_dict("records"),
            "reason": "Supplied model comparison; retrospective metrics, not independent validation."}


def get_feature_importance():
    from services.provider import get_service
    service = get_service()
    if service.demo:
        return {"available": False, "reason": "Verified feature importance is not connected in demo mode."}
    frame = service.feature_importance()
    return {"available": True, "data": frame.to_dict("records"),
            "reason": "Supplied Random Forest baseline importance; not tuned XGBoost explanations."}


def get_threshold_analysis(df):
    from services.analytics import threshold_curve
    return threshold_curve(df)


def generate_chart_spec(df, dimension, metric):
    if dimension not in df.columns or metric not in df.columns:
        raise ValueError("Unsupported chart fields")
    return {"kind": "bar", "dimension": dimension, "metric": metric,
            "data": aggregate(df, dimension, metric)}
