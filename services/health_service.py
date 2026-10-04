from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from config import DEMO_MODE


def checks(df):
    checked = datetime.now(ZoneInfo("Asia/Calcutta")).strftime("%d %b %Y %H:%M:%S IST")
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
    return pd.DataFrame([{"Component": a, "Status": b, "Last Check": checked, "Details": c, "Action": d} for a, b, c, d in values])

