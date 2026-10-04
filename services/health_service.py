from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from services.provider import get_service


def checks(df):
    checked = datetime.now(ZoneInfo("Asia/Calcutta")).strftime("%d %b %Y %H:%M:%S IST")
    service = get_service()
    if service.is_demo("delivery") and service.is_demo("demand"):
        values = [
        ("Application", "Operational", "UI runtime is active", "overview"),
        ("Data", "Demo UI", "Synthetic service active; no live data connected", "quality"),
        ("Delivery", "Demo UI", "Configured capability; model artifact not loaded in UI phase", "models"),
        ("Demand", "Demo UI", "Forecast interface uses fixtures; model artifact not loaded", "models"),
        ("Profitability", "Not Connected", "No verified profitability model connected", "profitability"),
        ("Prediction Engine", "Not Connected", "Live inference intentionally disabled", "models"),
        ("Metadata", "Partial", "No validation manifest connected", "lineage"),
        ("Cache", "Session-only", "Deterministic fixture cache; no production cache", "settings"),
        ]
    else:
        values = [
            ("Application", "Operational", "UI runtime is active", "overview"),
            ("Delivery data", "Connected CSV", "Pre-scored delivery rows connected; evaluation split provenance is unavailable", "delivery"),
            ("Demand data", "Connected CSV", "Precomputed product/day forecasts connected; interval coverage is below the source nominal label", "demand"),
            ("Delivery model", "Unavailable", "The serialized model artifact is absent and no inference is performed", "models"),
            ("Profitability", "Not Connected", "No verified profitability model connected", "profitability"),
            ("Prediction Engine", "Not Connected", "Only precomputed scored outputs are connected", "models"),
            ("Metadata", "Partial", "Threshold CSV is connected; training and validation manifest is incomplete", "lineage"),
            ("Cache", "Process cache", "CSV data cache keyed by file metadata; no shared cache", "settings"),
        ]
    return pd.DataFrame([{"Component": a, "Status": b, "Last Check": checked, "Details": c, "Action": d} for a, b, c, d in values])

