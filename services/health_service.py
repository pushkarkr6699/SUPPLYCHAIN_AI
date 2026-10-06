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
        from services.inference_service import status as delivery_status
        from services.demand_inference import status as demand_status
        from services.profitability_inference import status as profit_status
        from services.final_delivery_inference import status as final_status
        from services.ai_narration import status as ai_status
        delivery, demand = delivery_status(), demand_status()
        profit, ai = profit_status(), ai_status()
        values = [
            ("Application", "Operational", "UI runtime is active", "overview"),
            ("Delivery data", "Connected CSV", "Primary unique orders and partial January 2018 scores; test-selected threshold", "delivery"),
            ("Demand data", "Connected CSV", "Precomputed product/day forecasts connected; interval coverage is below the source nominal label", "demand"),
            ("Delivery model", "Validated" if delivery["available"] else "Unavailable", delivery["reason"], "scenarios"),
            ("Demand model", "Validated" if demand["available"] else "Unavailable", demand["reason"], "demand"),
            ("Profitability scores", "Connected CSV", "Registered line-item test scores and evaluation references", "profitability"),
            ("Profitability inference", "Validated" if profit["available"] else "Unavailable", profit["reason"], "profitability"),
            ("Final delivery inference", "Validated" if final_status()["available"] else "Unavailable", final_status()["reason"], "delivery"),
            ("Live AI", "Configured" if ai["available"] else "Not Connected", ai["reason"], "settings"),
            ("Prediction Engine", "Available" if delivery["available"] and demand["available"] else "Partial", "On-demand model execution uses registered artifacts and parity validation", "models"),
            ("Metadata", "Connected", "Source hashes, training provenance and runtime parity reports are registered", "lineage"),
            ("Cache", "Process cache", "CSV data cache keyed by file metadata; no shared cache", "settings"),
        ]
    return pd.DataFrame([{"Component": a, "Status": b, "Last Check": checked, "Details": c, "Action": d} for a, b, c, d in values])

