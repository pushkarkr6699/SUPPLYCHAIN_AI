"""Regenerate capability metadata from actual trained runtime validation."""
from pathlib import Path
import sys
import json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.inference_service import status as delivery_status, FEATURES as DELIVERY_FEATURES, MODEL_PATH
from services.demand_inference import status as demand_status, FEATURES as DEMAND_FEATURES, MODEL as DEMAND_MODEL

delivery, demand = delivery_status(), demand_status()
qa_path = ROOT / "metadata/release_status.json"
qa = json.loads(qa_path.read_text()) if qa_path.exists() else {}

def write(name, value):
    (ROOT / "metadata" / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

write("capability_matrix.json", {"version": 2, "capabilities": {
    "demo_ui": {"status": "available", "provider": "demo"},
    "delivery_primary_analytics": {"status": "connected", "rows": 65752, "grain": "unique order"},
    "delivery_pre_scored_analysis": {"status": "connected", "rows": 2123, "missing_scores": "preserved as null"},
    "demand_precomputed_forecasts": {"status": "connected", "rows": 2280, "units": "next-day web visits"},
    "delivery_live_inference": {"status": "available" if delivery["available"] else "disabled", **delivery},
    "demand_live_inference": {"status": "available" if demand["available"] else "disabled", **demand},
    "historical_sales_profit": {"status": "connected", "reason": "Recorded source values; no profitability prediction model"},
    "profitability": {"status": "unavailable", "reason": "No approved profitability model/scored output"},
    "cross_risk_join": {"status": "disabled", "reason": "No validated shared key/grain"},
    "shap": {"status": "unavailable", "reason": "No verified SHAP outputs"},
    "drift": {"status": "unavailable", "reason": "No reference/current operational windows"},
    "copilot": {"status": "available", "implementation": "deterministic source-aware analytics; no external LLM"},
    "public_production_authentication": {"status": "unavailable", "reason": "Session-only access flow preserved"},
    "local_classroom_showcase": {"status": qa.get("overall", "awaiting final QA"), "evidence": "QA_REPORT.md", "public_production_ready": False},
    "security_review": {"status": qa.get("security", "awaiting final QA"), "scope": "practical loopback-only showcase checks", "evidence": "SECURITY.md"}
}})
write("model_registry.json", {"registry_version": 2, "models": [
    {"id": "delivery_d1_tuned_xgboost", "display_name": "Tuned XGBoost", "artifact_path": MODEL_PATH,
     "status": "validated" if delivery["available"] else "disabled", "inference_enabled": delivery["available"],
     "decision_threshold": 0.35, "risk_boundaries": [0.4, 0.7], "features": DELIVERY_FEATURES,
     "validation_report": "metadata/inference_validation.json", "portable_registry": "metadata/portable_model_registry.json",
     "evaluation": "January 2018 test predictions; threshold selected on same test rows"},
    {"id": "delivery_d1_random_forest_baseline", "artifact_path": "models/delivery/DataCo_Late_Delivery_Model.pkl",
     "inference_enabled": False, "status": "reference_only", "explainability": "DataCo_Feature_Importance.csv belongs to this baseline"},
    {"id": "demand_d2_xgboost", "artifact_path": DEMAND_MODEL, "inference_enabled": demand["available"],
     "status": "validated" if demand["available"] else "disabled", "features": DEMAND_FEATURES,
     "target": "next-day web visits", "minimum_daily_history": 15,
     "validation_report": "metadata/demand_inference_validation.json", "portable_registry": "metadata/portable_demand_registry.json"},
    {"id": "delivery_d3_line_item_xgboost", "artifact_path": "models/delivery/d3/Final_Late_Delivery_Model.pkl",
     "status": "separate_reference", "inference_enabled": False, "decision_threshold": 0.56, "grain": "line item; incompatible with d1 model inputs"}
]})
write("project_schema.json", {"version": 2, "delivery": {"primary": "data/delivery/final/DataCo_Final_Order_Level_Dataset.csv",
    "grain": "unique Order Id", "join": "left one-to-one final scored outputs by Order Id, shared fields checked",
    "canonical_columns": {"Order": "Order Id", "Date": "Order_Date", "Actual Late": "Late_delivery_risk",
                          "Risk Probability": "Late_Delivery_Probability (nullable)", "Predicted Late": "Predicted_Late_Delivery (nullable)",
                          "Risk": "Risk_Level without Risk suffix (nullable)", "Profit": "Order Profit Per Order"}},
    "demand": {"grain": "Product + DateOnly", "date_semantics": "base date; predicts following day", "units": "web visits",
               "canonical_columns": {"Date": "DateOnly", "Actual Demand": "Next_Day_Visits", "Forecast Demand": "Predicted_Next_Day_Visits", "Lower": "Prediction_Lower_90", "Upper": "Prediction_Upper_90"}},
    "join_policy": "No delivery-to-demand join without validated shared grain/key."})
print("Capability, model and schema metadata refreshed from runtime validation.")
