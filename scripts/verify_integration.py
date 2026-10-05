"""Actual local artifacts, all routes and trained prediction controls smoke test."""
import os
os.environ["SUPPLYCHAIN_PROVIDER"] = "verified"
from pathlib import Path
import sys
import json
from hashlib import sha256
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
from components.navigation import ROUTES
from services.provider import get_service
from services.inference_service import status as delivery_status, input_rows, predict_delivery
from services.demand_inference import status as demand_status, registered, SOURCE, predict_next_day
import pandas as pd


def application(route):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for name, value in {"authenticated": True, "route": route, "route_initialized": True, "developer_mode": True}.items():
        at.session_state[name] = value
    return at.run()


def check(at, route):
    errors = [item.value for item in at.error if not (route == "diagnostics" and "Error-state preview" in item.value)]
    assert not at.exception and not errors, (route, [item.message for item in at.exception], errors)


manifest = json.loads((ROOT / "metadata/data_registry.json").read_text(encoding="utf-8"))
for row in manifest["artifacts"]:
    assert sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"], row["path"]
service = get_service()
delivery, demand = service.records(dataset="delivery"), service.records(dataset="demand")
assert len(delivery) == 65752 and delivery.Order.is_unique
assert delivery["Risk Probability"].notna().sum() == 2123 and len(demand) == 2280
assert delivery_status()["available"] and demand_status()["available"]
assert len(predict_delivery(input_rows([delivery.Order.iloc[0]]))) == 1
assert len(predict_next_day(pd.read_csv(registered(SOURCE)[0]))) == 76
for route in ["landing", "login", *ROUTES]:
    at = application(route)
    check(at, route)
    print(f"PASS {route}", flush=True)
    if route == "scenarios":
        next(button for button in at.button if button.label == "Run trained model").click().run()
        check(at, route)
        assert "verified_prediction_result" in at.session_state
    if route == "demand":
        at.button(key="run_demand_model").click().run()
        check(at, route)
        assert any("Predicted Visits" in table.value.columns for table in at.dataframe)
    if route in {"data", "quality"}:
        at.selectbox(key=f"{route}_dataset").select("demand").run()
        check(at, route)
        assert at.session_state.active_filter_dataset == "demand"
    if route == "copilot":
        at.button(key="prompt_2").click().run()
        check(at, route)
        response = at.session_state.conversation[-1]["response"]
        assert response["intent"] == "risk" and not response["table"].empty
        at.selectbox(key="copilot_dataset").select("demand").run()
        next(button for button in at.button if button.label == "Clear conversation").click().run()
        at.button(key="prompt_6").click().run()
        check(at, route)
        assert at.session_state.conversation[-1]["response"]["intent"] == "demand"
    if route == "reports":
        for report_type in ("Delivery", "Demand"):
            at.selectbox(key="report_type").select(report_type).run()
            next(button for button in at.button if button.label == "Generate PDF").click().run()
            check(at, route)
            assert at.session_state.generated_report[1].startswith(b"%PDF")
report = {"source_artifacts_verified": len(manifest["artifacts"]), "delivery_orders": len(delivery),
          "supplied_scored_orders": 2123, "demand_rows": len(demand), "routes_passed": len(ROUTES) + 2,
          "delivery_inference": delivery_status(), "demand_inference": demand_status(), "prediction_controls": "passed",
          "dataset_switches": "passed", "copilot_delivery_and_demand": "passed", "delivery_and_demand_pdf": "passed"}
(ROOT / "metadata/integration_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
