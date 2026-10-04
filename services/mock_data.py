"""ALL synthetic fixtures and illustrative analytical values live here.

DEMO UI DATA only. Deterministic, fictional records, no CSV/PKL access or ML.
Each row is a synthetic order/planning observation. Forecast quantities are
additive UI fixtures, not a claim about the grain of future production data.
"""
from functools import lru_cache
import numpy as np
import pandas as pd

DEMO_LABEL = "DEMO UI DATA"
DEMO_START = "2026-08-10"
DEMO_DAYS = 56
DEMO_AS_OF = "2026-10-04 09:00 IST · fixture snapshot"
MARKETS = {
    "Europe": [("Western Europe", "France"), ("Northern Europe", "Germany")],
    "LATAM": [("South America", "Brazil"), ("Central America", "Mexico")],
    "North America": [("US Central", "United States"), ("Canada", "Canada")],
    "Asia Pacific": [("South Asia", "India"), ("East Asia", "Japan")],
}
PRODUCTS = [
    ("Trail Runner", "Footwear", "Apparel"),
    ("Everyday Backpack", "Accessories", "Apparel"),
    ("Training Jacket", "Outerwear", "Apparel"),
    ("Performance Bicycle", "Cycling", "Sports"),
    ("Fitness Mat", "Fitness", "Sports"),
    ("Wireless Headphones", "Electronics", "Technology"),
]
SHIPPING = ["Standard Class", "Second Class", "First Class", "Same Day"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
RISK_LEVELS = ["Low", "Attention", "High", "Critical"]
FEATURES = pd.DataFrame({
    "Feature": ["Scheduled shipping days", "Shipping mode", "Order volume", "Market", "Category", "Customer segment"],
    "Importance": [0.31, 0.24, 0.17, 0.13, 0.09, 0.06],
    "Contribution": [0.17, 0.10, -0.07, 0.04, -0.03, 0.01],
})
MODEL_COMPARISON = pd.DataFrame({"Model": ["Logistic baseline", "Random forest", "XGBoost"], "Demo accuracy": [0.71, 0.79, 0.84]})
DEMAND_COMPARISON = pd.DataFrame({"Model": ["Seasonal naive", "Rolling baseline", "Forecast preview"], "Demo WAPE": [0.23, 0.18, 0.12]})
SCENARIO_FACTORS = {"Standard Class": 0.08, "Second Class": 0.03, "First Class": -0.06, "Same Day": -0.10}
SCENARIO_DEMAND_BASE = 240
LANDING_DEMO = {
    "delivery_risk": "24.8%",
    "delivery_caption": "High-risk deliveries · Demo",
    "demand_change": "+8.3%",
    "demand_caption": "Forecast outlook · Demo",
    "orders": "2,408",
    "forecast_units": "18.6k",
    "risk_points": [24, 30, 26, 42, 39, 47, 42, 56, 51, 62, 59, 72, 65, 81, 75, 91],
    "risk_distribution": [("Low", 48), ("Attention", 26), ("High", 18), ("Critical", 8)],
    "markets": ["Europe", "LATAM", "North America"],
    "critical_records": [("SC-10428", "EUROPE", "0.92", "Critical"), ("SC-10861", "LATAM", "0.87", "Critical"), ("SC-11034", "NORTH AMERICA", "0.79", "High")],
    "delivery_model": "Demo preview",
    "demand_model": "Demo preview",
    "copilot_question": "Show critical delivery risks.",
    "copilot_answer": "High-risk records appear in the selected markets. Open the evidence to inspect the demo records and filters behind this preview.",
    "copilot_metric_label": "High-risk demo records",
    "copilot_preview_badge": "Illustrative view",
    "evidence": "DEMO UI DATA · Synthetic records · No live model inference",
}
COPILOT_COPY = {
    "risk": "The table ranks delivery signals within your active context. These are synthetic observations for interface testing. Investigate the highest probabilities before comparing market averages.",
    "demand": "This product comparison summarizes synthetic actual demand, forecast demand and absolute forecast error. Prediction ranges are illustrative and are not calibrated confidence intervals.",
    "demand_growth": "Recent and earlier synthetic product demand averages are compared below. These observed differences are descriptive and do not predict future growth.",
    "market_risk": "Markets are ranked by mean synthetic delivery-risk probability. The record counts provide context; this is a descriptive model signal, not a causal explanation.",
    "region_risk": "Regions are ranked by mean synthetic delivery-risk probability. The record counts provide context; this is a descriptive model signal, not a causal explanation.",
    "change": "The current and preceding halves of this filtered demo period are compared below. These are observed changes in synthetic records; they do not establish causes.",
    "explain": "A real explanation is unavailable until a verified explanation artifact is connected. You can inspect the selected demo record and the clearly labeled illustrative feature-contribution view.",
    "unsupported": "This offline interface preview supports the suggested investigations only. No language model or external provider is connected. Try a risk, demand, comparison or explanation prompt.",
    "compare": "Europe and LATAM are compared within the active filters. Differences describe synthetic model signals and do not establish causality.",
}


@lru_cache(maxsize=1)
def fixture_records() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for day_no, day in enumerate(pd.date_range(DEMO_START, periods=DEMO_DAYS)):
        for market_no, (market, geos) in enumerate(MARKETS.items()):
            for prod_no, (product, category, department) in enumerate(PRODUCTS):
                region, country = geos[(day_no + prod_no) % len(geos)]
                shipping = SHIPPING[int(rng.integers(len(SHIPPING)))]
                risk = float(np.clip(rng.beta(2.2 + market_no * .2, 2.8) + (.10 if shipping == "Same Day" else 0), .03, .98))
                actual = max(1, int(30 + prod_no * 9 + day_no * .3 + 10 * np.sin(day_no * 2 * np.pi / 7) + rng.normal(0, 7)))
                forecast = max(1, int(actual * rng.normal(1.03, .16)))
                rows.append({
                    "Order": f"SC-{10400 + len(rows)}", "Date": day,
                    "Market": market, "Region": region, "Country": country,
                    "Product": product, "Category": category, "Department": department,
                    "Shipping Mode": shipping, "Customer Segment": SEGMENTS[int(rng.integers(3))],
                    "Risk Probability": round(risk, 4),
                    "Risk": "Critical" if risk >= .8 else "High" if risk >= .65 else "Attention" if risk >= .4 else "Low",
                    "Actual Late": bool(rng.random() < risk),
                    "Actual Demand": actual, "Forecast Demand": forecast,
                    "Lower": max(0, round(forecast * .78)), "Upper": round(forecast * 1.22),
                    "Stock Attention": forecast > actual * 1.15,
                    "Source": DEMO_LABEL,
                })
    return pd.DataFrame(rows)


def model_status() -> list[dict]:
    return [
        {"Model": "Delivery", "Status": "Demo state", "Artifact": "Not loaded", "Version": "demo-ui-v1", "Capability": "Trained capability reported; UI uses fixtures"},
        {"Model": "Demand", "Status": "Demo state", "Artifact": "Not loaded", "Version": "demo-ui-v1", "Capability": "Trained capability reported; UI uses fixtures"},
        {"Model": "Profitability", "Status": "Not connected", "Artifact": "Unavailable", "Version": "—", "Capability": "No verified artifact"},
    ]

